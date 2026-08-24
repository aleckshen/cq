from cq.tui import CqApp, MenuScreen, QuizScreen, ResultsScreen


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
