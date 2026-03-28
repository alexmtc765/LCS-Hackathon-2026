def format_seconds(seconds: float) -> str:
    """Render seconds as MM:SS for timer UI."""
    whole = max(0, int(seconds))
    return f"{whole // 60:02d}:{whole % 60:02d}"


def build_interval_queue(task: dict) -> list[dict]:
    """
    Build a work/break sequence from task inputs.

    Rules:
    - If breaks == 0: one single work interval.
    - If breaks == N > 0:
      - Work minutes are split into N + 1 equal work chunks.
      - Total break minutes are split into N equal break chunks.
      - Intervals alternate work and break, ending on work.
    """
    total_work_minutes = float(task["total_work_minutes"])
    number_of_breaks = int(task["number_of_breaks"])
    total_break_minutes = float(task["total_break_minutes"])

    total_work_seconds = total_work_minutes * 60.0
    total_break_seconds = total_break_minutes * 60.0

    if number_of_breaks == 0:
        return [
            {
                "kind": "work",
                "seconds": total_work_seconds,
                "label": "Work 1/1",
            }
        ]

    work_chunks = number_of_breaks + 1
    work_chunk_seconds = total_work_seconds / work_chunks
    break_chunk_seconds = total_break_seconds / number_of_breaks

    queue: list[dict] = []
    for idx in range(work_chunks):
        queue.append(
            {
                "kind": "work",
                "seconds": work_chunk_seconds,
                "label": f"Work {idx + 1}/{work_chunks}",
            }
        )
        if idx < number_of_breaks:
            queue.append(
                {
                    "kind": "break",
                    "seconds": break_chunk_seconds,
                    "label": f"Break {idx + 1}/{number_of_breaks}",
                }
            )

    return queue
