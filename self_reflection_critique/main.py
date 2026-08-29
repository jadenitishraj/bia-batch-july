"""Command-line runner for the writing critic practical.

The draft is pasted into the terminal by whoever runs the demo. The brief,
rubric and constitution stay on disk: those are the standards, and every run
has to be graded against the same bar for the scores to mean anything.
"""

from __future__ import annotations

from critic_loop import (
    print_iteration_trace,
    read_text,
    run_refinement_loop,
    save_demo_outputs,
)
from schemas import IterationRecord

PASS_SCORE = 8
MAX_ITERATIONS = 3
END_WORDS = {"END", "DONE"}
MAX_INPUT_LINES = 300
LINE = "=" * 78


def prompt_for_draft() -> str:
    """Read a multi-line draft pasted into the terminal.

    Stops on END (or DONE) on a line of its own, on two blank lines in a row,
    or on end of input. It can never loop forever.

    Params:
        None.
    Returns:
        The pasted text with surrounding whitespace stripped.
    """
    print(LINE)
    print("Paste the draft you want the critic to improve.")
    print("To finish: type END on a line of its own, or press Enter twice.")
    print(LINE)

    lines: list[str] = []
    blanks = 0

    for _ in range(MAX_INPUT_LINES):
        try:
            chunk = input("draft (END to finish) > ")
        except EOFError:
            break
        except KeyboardInterrupt:
            print("\nCancelled. Nothing was sent to the model.")
            raise SystemExit(1) from None

        finished = False
        # Some terminals and notebook frontends hand back a whole paste at once.
        for line in chunk.splitlines() or [""]:
            if line.strip().upper() in END_WORDS:
                finished = True
                break
            blanks = 0 if line.strip() else blanks + 1
            lines.append(line)

        if finished or blanks >= 2:
            break

    return "\n".join(lines).strip()


def print_result(final_draft: str, trace: list[IterationRecord], pass_score: int) -> None:
    """Print the outcome of the loop without overstating it.

    A run that never reached the pass mark is labelled as such. The plateau is
    the most useful thing the demo shows, so it must stay visible.

    Params:
        final_draft: Draft returned by the loop.
        trace: Iteration records from the loop.
        pass_score: Score the draft had to reach.
    Returns:
        None.
    """
    scores = " -> ".join(str(record.score) for record in trace)
    last = trace[-1]

    print("\n" + LINE)
    if last.passed:
        print(f"RESULT: PASSED — {last.score}/10 on round {last.iteration} "
              f"(pass mark {pass_score}/10)")
        print(f"Round scores: {scores}")
        print(LINE)
        print("\nFINAL DRAFT\n")
    else:
        best = max(record.score for record in trace)
        print(f"RESULT: NOT PASSED — best score {best}/10, pass mark {pass_score}/10")
        print(f"Round scores: {scores}")
        print(f"Stopped after {len(trace)} rounds without reaching the pass mark.")
        print(LINE)
        print("\nThe text below is the rewrite made after the last critique.")
        print("It was never scored — the retry budget ran out first.\n")
        print("DRAFT AS IT STANDS — NOT PASSED\n")

    print(final_draft)


def main() -> None:
    """Run the full practical on a draft pasted into the terminal.

    Params:
        None.
    Returns:
        None.
    """
    brief = read_text("data/writing_brief.txt")
    rubric = read_text("data/rubric.md")
    constitution = read_text("data/constitution.md")

    draft = prompt_for_draft()
    if not draft:
        print("\nNo draft was entered, so there is nothing to critique.")
        print("Nothing was sent to the model. Run the script again and paste some text.")
        raise SystemExit(1)

    print(f"\nGot a draft of {len(draft.split())} words. Scoring it now...\n")

    final_draft, trace = run_refinement_loop(
        brief=brief,
        initial_draft=draft,
        rubric=rubric,
        constitution=constitution,
        pass_score=PASS_SCORE,
        max_iterations=MAX_ITERATIONS,
    )

    print_iteration_trace(trace)
    print_result(final_draft, trace, PASS_SCORE)

    save_demo_outputs(final_draft, trace)


if __name__ == "__main__":
    main()
