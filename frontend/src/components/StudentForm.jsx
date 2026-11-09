export default function StudentForm({
    value,
    onChange,
    onSubmit,
    onRefresh,
    disabled,
    loading,
}) {
    return (
        <form className="student-form" onSubmit={onSubmit}>
            <label htmlFor="student-id">Mã sinh viên</label>
            <input id="student-id" value={value} maxLength={8} required
                inputMode="numeric" onChange={(event) => onChange(event.target.value)}
                disabled={disabled} />
            <button type="submit" disabled={disabled}>Xem đăng ký</button>
            <button type="button" className="secondary"
                disabled={disabled || loading} onClick={onRefresh}>
                Tải lại dữ liệu
            </button>
        </form>
    );
}
