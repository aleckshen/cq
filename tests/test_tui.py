from textual.widgets import Static

from cq.tui import CqApp, MenuList, MenuScreen, QuizScreen, ResultsScreen


async def test_menu_shows_and_selecting_opens_quiz() -> None:
    app = CqApp()
    async with app.run_test() as pilot:
        assert isinstance(app.screen, MenuScreen)
        await pilot.press("enter")
        assert isinstance(app.screen, QuizScreen)


async def test_typing_a_country_scores_without_pressing_enter() -> None:
    app = CqApp()
    async with app.run_test() as pilot:
        await pilot.press("enter")  # open the quiz
        screen = app.screen
        assert isinstance(screen, QuizScreen)

        await pilot.press(*"france")
        assert screen.quiz.score == 1
        assert screen.query_one("Input").value == ""


async def test_timer_and_score_are_both_on_screen() -> None:
    # Regression: unset `width` on Static defaults to filling the container,
    # so two Statics side by side in a Horizontal push the second off-screen
    # unless both are explicitly `width: auto`.
    app = CqApp()
    async with app.run_test(size=(90, 30)) as pilot:
        await pilot.press("enter")
        screen = app.screen
        assert isinstance(screen, QuizScreen)

        timer = screen.query_one("#timer", Static)
        score = screen.query_one("#score", Static)
        assert timer.region.right <= app.size.width
        assert score.region.right <= app.size.width
        assert score.region.x >= timer.region.right


async def test_incorrect_guess_leaves_text_and_score_unchanged() -> None:
    app = CqApp()
    async with app.run_test() as pilot:
        await pilot.press("enter")
        screen = app.screen
        assert isinstance(screen, QuizScreen)

        await pilot.press(*"zzz")
        assert screen.quiz.score == 0
        assert screen.query_one("Input").value == "zzz"


async def test_finishing_the_quiz_shows_results() -> None:
    app = CqApp()
    async with app.run_test() as pilot:
        await pilot.press("enter")
        screen = app.screen
        assert isinstance(screen, QuizScreen)

        # Force completion without typing all 195 countries.
        for country in screen.quiz.countries:
            screen.quiz.answered.add(country.id)
        screen.finish()
        await pilot.pause()

        assert isinstance(app.screen, ResultsScreen)
        await pilot.press("escape")
        assert isinstance(app.screen, MenuScreen)


async def test_finish_is_idempotent() -> None:
    # Regression: on_tick and on_input_changed can both land on the last
    # country, and two switch_screen calls would stack two results screens.
    app = CqApp()
    async with app.run_test() as pilot:
        await pilot.press("enter")
        screen = app.screen
        assert isinstance(screen, QuizScreen)

        depth = len(app.screen_stack)
        screen.finish()
        screen.finish()
        await pilot.pause()

        assert isinstance(app.screen, ResultsScreen)
        assert len(app.screen_stack) == depth


async def test_escape_abandons_the_quiz() -> None:
    app = CqApp()
    async with app.run_test() as pilot:
        await pilot.press("enter")
        assert isinstance(app.screen, QuizScreen)

        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, ResultsScreen)


async def test_ctrl_r_restarts_the_quiz() -> None:
    app = CqApp()
    async with app.run_test() as pilot:
        await pilot.press("enter")
        first = app.screen
        assert isinstance(first, QuizScreen)
        await pilot.press(*"france")
        assert first.quiz.score == 1

        await pilot.press("ctrl+r")
        await pilot.pause()
        second = app.screen
        assert isinstance(second, QuizScreen)
        assert second is not first
        assert second.quiz.score == 0


async def test_menu_selection_wraps_around() -> None:
    app = CqApp()
    async with app.run_test() as pilot:
        screen = app.screen
        assert isinstance(screen, MenuScreen)
        menu = screen.query_one(MenuList)

        await pilot.press("up")  # wrap backwards onto "quit"
        assert menu.index == len(menu.entries) - 1
        await pilot.press("enter")
        await pilot.pause()
        assert not app.is_running


async def test_menu_can_start_a_region_quiz() -> None:
    app = CqApp()
    async with app.run_test() as pilot:
        screen = app.screen
        assert isinstance(screen, MenuScreen)

        await pilot.press("down")  # first region after "the whole world"
        await pilot.press("enter")
        quiz = app.screen
        assert isinstance(quiz, QuizScreen)
        assert 0 < len(quiz.countries) < 195
        assert len({c.region for c in quiz.countries}) == 1
