const dateFormatter = new Intl.DateTimeFormat("vi-VN", {
    dateStyle: "short",
    timeStyle: "short",
});

export default function EnrollmentHistory({
    rows,
    loading,
    error,
    page,
    hasNext,
    onPageChange,
}) {
    return (
        <section className="panel">
            <h2>4. Lịch sử đăng ký demo</h2>
            {loading && <p role="status">Đang tải lịch sử...</p>}
            {!loading && error && <p role="alert" className="error">{error}</p>}
            {!loading && !error && rows.length === 0 && (
                <p>Sinh viên chưa có nhật ký đăng ký demo.</p>
            )}
            {!loading && !error && rows.length > 0 && (
                <>
                    <div className="table-scroll">
                        <table aria-label="Lịch sử đăng ký demo">
                            <thead>
                                <tr>
                                    <th>Thời gian</th>
                                    <th>Lớp học phần</th>
                                    <th>Thao tác</th>
                                    <th>Nguồn</th>
                                </tr>
                            </thead>
                            <tbody>
                                {rows.map((row) => (
                                    <tr key={row.id}>
                                        <td>{dateFormatter.format(new Date(row.occurred_at))}</td>
                                        <td>{row.class_section_id}</td>
                                        <td>{row.event_type === "CREATED"
                                            ? "Đăng ký" : "Hủy đăng ký"}</td>
                                        <td>{row.source}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                    <nav className="history-pagination" aria-label="Phân trang lịch sử">
                        <button type="button" className="secondary"
                            disabled={page === 0} onClick={() => onPageChange(page - 1)}>
                            Trang trước
                        </button>
                        <span>Trang {page + 1}</span>
                        <button type="button" className="secondary"
                            disabled={!hasNext} onClick={() => onPageChange(page + 1)}>
                            Trang sau
                        </button>
                    </nav>
                </>
            )}
        </section>
    );
}
