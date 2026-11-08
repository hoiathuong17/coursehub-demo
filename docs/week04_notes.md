# CourseHub - Buoi 4
- Migration 001: enrollment_events.
- Demo class: RACE-01, capacity = 1.
- POST /enrollments: lock class_sections bang FOR UPDATE.
- Concurrency test: 1 request 201, 1 request 409.
- Performance data: 100000 rows, dataset=performance.
- Index: idx_enrollment_events_dataset_student_time.
- Ghi lai scan type va Execution Time truoc/sau o day.
Khong commit backend/.env.


Chưa có index:
"Limit  (cost=2913.83..2913.95 rows=50 width=39) (actual time=20.055..20.068 rows=50 loops=1)"
"  Buffers: shared hit=1137"
"  ->  Sort  (cost=2913.83..2915.84 rows=807 width=39) (actual time=20.052..20.058 rows=50 loops=1)"
"        Sort Key: occurred_at DESC"
"        Sort Method: top-N heapsort  Memory: 31kB"
"        Buffers: shared hit=1137"
"        ->  Seq Scan on enrollment_events  (cost=0.00..2887.02 rows=807 width=39) (actual time=0.101..19.680 rows=820 loops=1)"
"              Filter: ((occurred_at >= '2025-12-20 00:00:00'::timestamp without time zone) AND ((dataset)::text = 'performance'::text) AND ((student_id)::text = '22000001'::text))"
"              Rows Removed by Filter: 99181"
"              Buffers: shared hit=1137"
"Planning:"
"  Buffers: shared hit=5 dirtied=1"
"Planning Time: 1.909 ms"
"Execution Time: 20.112 ms"
có index:
"Limit  (cost=0.42..67.60 rows=50 width=39) (actual time=0.134..0.201 rows=50 loops=1)"
"  Buffers: shared hit=50 read=3"
"  ->  Index Scan using idx_enrollment_events_dataset_student_time on enrollment_events  (cost=0.42..1114.38 rows=829 width=39) (actual time=0.133..0.192 rows=50 loops=1)"
"        Index Cond: (((dataset)::text = 'performance'::text) AND ((student_id)::text = '22000001'::text) AND (occurred_at >= '2025-12-20 00:00:00'::timestamp without time zone))"
"        Buffers: shared hit=50 read=3"
"Planning:"
"  Buffers: shared hit=39 read=1"
"Planning Time: 3.250 ms"
Execution Time: 0.227 ms


