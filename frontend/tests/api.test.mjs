import assert from "node:assert/strict";
import { test } from "node:test";
import { api } from "../src/api.js";

function mockResponse({ status = 200, ok = status >= 200 && status < 300, body = "" } = {}) {
    return {
        status,
        ok,
        text: async () => body,
    };
}

test("sends a GET request by default and returns parsed JSON", async (t) => {
    const fetch = t.mock.method(globalThis, "fetch", async () =>
        mockResponse({ body: '[{"code":"INT2204"}]' }),
    );

    const result = await api("/courses");

    assert.deepEqual(result, [{ code: "INT2204" }]);
    assert.deepEqual(fetch.mock.calls[0].arguments, [
        "http://127.0.0.1:8000/courses",
        {
            method: "GET",
            signal: undefined,
            headers: {},
            body: undefined,
        },
    ]);
});

test("serializes request bodies and forwards method and abort signal", async (t) => {
    const payload = { student_id: "22000004", class_section_id: "WEB-02" };
    const signal = new AbortController().signal;
    const fetch = t.mock.method(globalThis, "fetch", async () =>
        mockResponse({ status: 201, body: '{"message":"Dang ky thanh cong"}' }),
    );

    const result = await api("/enrollments", {
        method: "POST",
        body: payload,
        signal,
    });

    assert.deepEqual(result, { message: "Dang ky thanh cong" });
    assert.deepEqual(fetch.mock.calls[0].arguments, [
        "http://127.0.0.1:8000/enrollments",
        {
            method: "POST",
            signal,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        },
    ]);
});

test("returns null for a successful 204 without reading a response body", async (t) => {
    const response = {
        status: 204,
        ok: true,
        text: t.mock.fn(async () => {
            throw new Error("204 responses must not be read");
        }),
    };
    t.mock.method(globalThis, "fetch", async () => response);

    assert.equal(await api("/enrollments/22000004/WEB-02", { method: "DELETE" }), null);
    assert.equal(response.text.mock.callCount(), 0);
});

test("returns null for an empty successful response", async (t) => {
    t.mock.method(globalThis, "fetch", async () => mockResponse());

    assert.equal(await api("/courses"), null);
});

test("formats validation error details and preserves the HTTP status", async (t) => {
    t.mock.method(globalThis, "fetch", async () =>
        mockResponse({
            status: 422,
            ok: false,
            body: JSON.stringify({
                detail: [
                    { msg: "Field required" },
                    { msg: "String should have at least 8 characters" },
                ],
            }),
        }),
    );

    await assert.rejects(api("/enrollments", { method: "POST", body: {} }), (error) => {
        assert.equal(error.message, "HTTP 422: Field required; String should have at least 8 characters");
        assert.equal(error.status, 422);
        return true;
    });
});

test("formats string error details", async (t) => {
    t.mock.method(globalThis, "fetch", async () =>
        mockResponse({
            status: 404,
            ok: false,
            body: JSON.stringify({ detail: "Khong tim thay sinh vien" }),
        }),
    );

    await assert.rejects(api("/students/missing/enrollments"), {
        message: "HTTP 404: Khong tim thay sinh vien",
        status: 404,
    });
});

for (const [label, body] of [
    ["missing details", "{}"],
    ["non-string details", '{"detail":{"message":"failure"}}'],
    ["an empty body", ""],
]) {
    test(`uses a fallback for ${label}`, async (t) => {
        t.mock.method(globalThis, "fetch", async () =>
            mockResponse({ status: 500, ok: false, body }),
        );

        await assert.rejects(api("/courses"), {
            message: "HTTP 500: Yêu cầu không thành công.",
            status: 500,
        });
    });
}

test("rejects malformed JSON responses with the HTTP status", async (t) => {
    t.mock.method(globalThis, "fetch", async () =>
        mockResponse({ status: 200, body: "<html>not JSON</html>" }),
    );

    await assert.rejects(api("/courses"), {
        message: "HTTP 200: phản hồi không phải JSON.",
    });
});

test("reports a non-JSON error response instead of masking it", async (t) => {
    t.mock.method(globalThis, "fetch", async () =>
        mockResponse({ status: 502, ok: false, body: "Bad Gateway" }),
    );

    await assert.rejects(api("/courses"), {
        message: "HTTP 502: phản hồi không phải JSON.",
    });
});

test("rethrows abort errors without logging or wrapping them", async (t) => {
    const abortError = new Error("The operation was aborted");
    abortError.name = "AbortError";
    t.mock.method(globalThis, "fetch", async () => {
        throw abortError;
    });
    const logError = t.mock.method(console, "error");

    await assert.rejects(api("/courses"), (error) => error === abortError);
    assert.equal(logError.mock.callCount(), 0);
});

test("logs and wraps other network errors", async (t) => {
    const networkError = new Error("fetch failed");
    t.mock.method(globalThis, "fetch", async () => {
        throw networkError;
    });
    const logError = t.mock.method(console, "error", () => {});

    await assert.rejects(api("/courses"), {
        message:
            "Không nhận được phản hồi API (fetch failed). Kiểm tra Backend/CORS và tải lại dữ liệu trước khi gửi lại thao tác.",
    });
    assert.deepEqual(logError.mock.calls[0].arguments, ["Lỗi kết nối API:", networkError]);
});
