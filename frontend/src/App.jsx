import { useEffect, useState } from "react";
import { api } from "./api.js";
import Notice from "./components/Notice.jsx";
import SectionTable from "./components/SectionTable.jsx";
import EnrollmentList from "./components/EnrollmentList.jsx";
import StudentForm from "./components/StudentForm.jsx";
import EnrollmentHistory from "./components/EnrollmentHistory.jsx";

const HISTORY_PAGE_SIZE = 20;
const SECTION_PAGE_SIZE = 20;

export default function App() {
    const [draftId, setDraftId] = useState("22000004");
    const [studentId, setStudentId] = useState("22000004");
    const [courses, setCourses] = useState([]);
    const [sections, setSections] = useState([]);
    const [sectionPage, setSectionPage] = useState(0);
    const [sectionHasNext, setSectionHasNext] = useState(false);
    const [sectionsLoading, setSectionsLoading] = useState(true);
    const [sectionsError, setSectionsError] = useState("");
    const [enrollments, setEnrollments] = useState([]);
    const [historyRows, setHistoryRows] = useState([]);
    const [historyPage, setHistoryPage] = useState(0);
    const [historyHasNext, setHistoryHasNext] = useState(false);
    const [historyLoading, setHistoryLoading] = useState(true);
    const [historyError, setHistoryError] = useState("");
    const [search, setSearch] = useState("");
    const [courseCode, setCourseCode] = useState("");
    const [onlyAvailable, setOnlyAvailable] = useState(false);
    const [loading, setLoading] = useState(true);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState("");
    const [notice, setNotice] = useState({ kind: "info", text: "" });
    const [refresh, setRefresh] = useState(0);
    useEffect(() => {
        const controller = new AbortController();
        const options = { signal: controller.signal };
        async function loadData() {
            setLoading(true);
            setError("");
            try {
                const [courseData, enrollmentData] = await Promise.all([
                    api("/courses", options),
                    api(`/students/${encodeURIComponent(studentId)}/enrollments`,
                        options),
                ]);
                if (controller.signal.aborted) return;
                setCourses(courseData);
                setEnrollments(enrollmentData);
            } catch (err) {
                if (controller.signal.aborted) return;
                setError(err.message);
                setCourses([]);
                setEnrollments([]);
            } finally {
                if (!controller.signal.aborted) setLoading(false);
            }
        }
        loadData();
        return () => controller.abort();
    }, [studentId, refresh]);
    useEffect(() => {
        const controller = new AbortController();
        const params = new URLSearchParams({
            limit: String(SECTION_PAGE_SIZE + 1),
            skip: String(sectionPage * SECTION_PAGE_SIZE),
            available_only: String(onlyAvailable),
        });
        if (search.trim()) params.set("q", search.trim());
        if (courseCode) params.set("course_code", courseCode);
        async function loadSections() {
            setSectionsLoading(true);
            setSectionsError("");
            try {
                const data = await api(`/sections?${params}`, {
                    signal: controller.signal,
                });
                if (controller.signal.aborted) return;
                if (!Array.isArray(data)) {
                    throw new Error("API danh sách lớp trả về dữ liệu không hợp lệ.");
                }
                setSections(data.slice(0, SECTION_PAGE_SIZE));
                setSectionHasNext(data.length > SECTION_PAGE_SIZE);
            } catch (err) {
                if (controller.signal.aborted) return;
                setSectionsError(err.message);
                setSections([]);
                setSectionHasNext(false);
            } finally {
                if (!controller.signal.aborted) setSectionsLoading(false);
            }
        }
        loadSections();
        return () => controller.abort();
    }, [search, courseCode, onlyAvailable, sectionPage, refresh]);
    useEffect(() => {
        const controller = new AbortController();
        async function loadHistory() {
            setHistoryLoading(true);
            setHistoryError("");
            const params = new URLSearchParams({
                student_id: studentId,
                limit: String(HISTORY_PAGE_SIZE + 1),
                skip: String(historyPage * HISTORY_PAGE_SIZE),
            });
            try {
                const events = await api(`/enrollment-events?${params}`, {
                    signal: controller.signal,
                });
                if (controller.signal.aborted) return;
                if (!Array.isArray(events)) {
                    throw new Error("API lịch sử trả về dữ liệu không hợp lệ.");
                }
                setHistoryRows(events.slice(0, HISTORY_PAGE_SIZE));
                setHistoryHasNext(events.length > HISTORY_PAGE_SIZE);
            } catch (err) {
                if (controller.signal.aborted) return;
                setHistoryError(err.message);
                setHistoryRows([]);
                setHistoryHasNext(false);
            } finally {
                if (!controller.signal.aborted) setHistoryLoading(false);
            }
        }
        loadHistory();
        return () => controller.abort();
    }, [studentId, historyPage, refresh]);
    function chooseStudent(event) {
        event.preventDefault();
        const nextId = draftId.trim();
        if (!/^\d{8}$/.test(nextId)) {
            setNotice({ kind: "error", text: "Mã demo phải gồm 8 chữ số." });
            return;
        }
        setNotice({ kind: "info", text: "" });
        setLoading(true);
        setHistoryPage(0);
        setStudentId(nextId);
        setRefresh((value) => value + 1);
    }
    async function changeEnrollment(sectionId, cancel = false) {
        if (busy || loading || error) return;
        if (cancel && !window.confirm(`Hủy đăng ký lớp ${sectionId}?`)) return;
        setBusy(true);
        setNotice({ kind: "info", text: "Đang gửi yêu cầu..." });
        try {
            if (cancel) {
                await api(
                    `/enrollments/${encodeURIComponent(studentId)}/${encodeURIComponent(sectionId)}`
                    ,
                    { method: "DELETE" },
                );
            } else {
                await api("/enrollments", {
                    method: "POST",
                    body: { student_id: studentId, class_section_id: sectionId },
                });
            }
            setNotice({
                kind: "success", text: cancel
                    ? `Đã hủy đăng ký ${sectionId}.`
                    : `Đăng ký ${sectionId} thành công.`
            });
        } catch (err) {
            setNotice({ kind: "error", text: err.message });
        } finally {
            // Đọc lại CSDL kể cả sau lỗi; không tự cộng/trừ số chỗ ở giao diện.
            setLoading(true);
            setRefresh((value) => value + 1);
            setBusy(false);
        }
    }
    const rows = sections.map((section) => ({
        ...section,
        registered: enrollments.some((item) => item.class_section_id ===
            section.class_id),
    }));
    const filterableCourses = courses.filter((course) =>
        ["INT2204", "INT2205", "INT2206"].includes(course.code)
    );
    const disabled = loading || busy || Boolean(error);
    return (
        <main className="container">
            <header className="hero">
                <p className="eyebrow">CSDL WEB VÀ HỆ THỐNG THÔNG TIN · BUỔI 5</p>
                <h1>CourseHub</h1>
                <p>Tra cứu và đăng ký lớp học phần</p>
                <span className="chip">React → FastAPI → PostgreSQL</span>
            </header>
            <p className="demo-note">
                Môi trường thực hành. Nhập mã sinh viên để thử dữ liệu, không phải đăng
                nhập.
            </p>
            <section className="panel">
                <h2>1. Chọn sinh viên</h2>
                <StudentForm value={draftId}
                    onChange={setDraftId}
                    onSubmit={chooseStudent}
                    onRefresh={() => setRefresh((value) => value + 1)}
                    disabled={busy}
                    loading={loading} />
                <p className="muted">Dữ liệu đang xem: <strong>{studentId}</strong>.
                    Mã mẫu: 22000001–22000004.</p>
            </section>
            <Notice kind={notice.kind}>{notice.text}</Notice>
            <Notice kind="error">{error}</Notice>
            {loading && <Notice>Đang tải dữ liệu từ API...</Notice>}
            {!loading && !error && (
                <div className="workspace">
                    <section className="panel">
                        <h2>2. Danh sách lớp học phần</h2>
                        <div className="filters">
                            <label htmlFor="search">Tìm lớp / học phần</label>
                            <input id="search" value={search} placeholder="Ví dụ: web"
                                onChange={(e) => {
                                    setSearch(e.target.value);
                                    setSectionPage(0);
                                }} />
                            <label htmlFor="course-code">Mã học phần</label>
                            <select id="course-code" value={courseCode}
                                onChange={(e) => {
                                    setCourseCode(e.target.value);
                                    setSectionPage(0);
                                }}>
                                <option value="">Tất cả học phần</option>
                                {filterableCourses.map((course) => (
                                    <option key={course.code} value={course.code}>
                                        {course.code}
                                    </option>
                                ))}
                            </select>
                            <label className="check">
                                <input type="checkbox" checked={onlyAvailable}
                                    onChange={(e) => {
                                        setOnlyAvailable(e.target.checked);
                                        setSectionPage(0);
                                    }} />
                                Chỉ hiện lớp còn chỗ
                            </label>
                        </div>
                        {sectionsError && <p role="alert" className="error">{sectionsError}</p>}
                        {sectionsLoading
                            ? <p role="status">Đang tải danh sách lớp...</p>
                            : !sectionsError && (
                                <>
                                    <SectionTable rows={rows} disabled={disabled}
                                        onEnroll={(id) => changeEnrollment(id)} />
                                    <nav className="history-pagination"
                                        aria-label="Phân trang danh sách lớp">
                                        <button type="button" className="secondary"
                                            disabled={sectionPage === 0}
                                            onClick={() => setSectionPage((page) => page - 1)}>
                                            Trang trước
                                        </button>
                                        <span>Trang {sectionPage + 1}</span>
                                        <button type="button" className="secondary"
                                            disabled={!sectionHasNext}
                                            onClick={() => setSectionPage((page) => page + 1)}>
                                            Trang sau
                                        </button>
                                    </nav>
                                </>
                            )}
                    </section>
                    <section className="panel">
                        <h2>3. Lớp đã đăng ký</h2>
                        <p className="muted">Sinh viên {studentId} · {enrollments.length}
                            lớp</p>
                        <EnrollmentList rows={enrollments} disabled={disabled}
                            onCancel={(id) => changeEnrollment(id, true)} />
                    </section>
                </div>
            )}
            {!loading && !error && (
                <EnrollmentHistory rows={historyRows}
                    loading={historyLoading}
                    error={historyError}
                    page={historyPage}
                    hasNext={historyHasNext}
                    onPageChange={setHistoryPage} />
            )}
            <footer>Số chỗ và đăng ký được đọc từ API; Backend quyết định tính hợp
                lệ.</footer>
        </main>
    );
}