from __future__ import annotations

from PySide6.QtCore import Qt

from music_downloader.models import SearchResult, SearchStatus
from music_downloader.ui.review_model import ReviewListModel, format_duration


def found(query: str, *, identifier: str = "id") -> SearchResult:
    return SearchResult(
        query=query,
        status=SearchStatus.FOUND,
        title=f"Title {query}",
        channel="Channel",
        duration=125,
        id=identifier,
        url=f"https://video.example/{identifier}",
    )


def test_model_preserves_order_and_selects_only_found_results(qtbot) -> None:
    model = ReviewListModel()
    results = (
        found("One", identifier="one"),
        SearchResult(query="Missing", status=SearchStatus.NO_RESULT),
        found("Two", identifier="two"),
    )

    model.reset_results(results)

    assert model.results == list(results)
    assert model.selected_count == 2
    assert model.data(model.index(0), Qt.ItemDataRole.CheckStateRole) == Qt.CheckState.Checked
    assert not (model.flags(model.index(1)) & Qt.ItemFlag.ItemIsUserCheckable)


def test_selection_emits_count_and_approved_results_keep_url_and_id(qtbot) -> None:
    model = ReviewListModel()
    model.reset_results((found("One", identifier="approved"), found("Two")))
    counts: list[int] = []
    model.selectionCountChanged.connect(counts.append)

    model.setData(
        model.index(1), Qt.CheckState.Unchecked, Qt.ItemDataRole.CheckStateRole
    )
    approved, rows = model.selected_results()

    assert counts[-1] == 1
    assert rows == [0]
    assert approved[0].id == "approved"
    assert approved[0].url == "https://video.example/approved"


def test_edit_query_invalidates_selection_without_mutating_original_result() -> None:
    model = ReviewListModel()
    original = found("Original", identifier="stable")
    model.reset_results((original,))

    assert model.edit_query(0, "Edited")

    edited = model.results[0]
    assert original.id == "stable"
    assert edited.query == "Edited"
    assert edited.status is SearchStatus.NO_RESULT
    assert edited.id is None
    assert model.selected_count == 0
    assert model.data(model.index(0), model.StatusRole).startswith("Editado")


def test_research_result_replaces_row_and_restores_approval() -> None:
    model = ReviewListModel()
    model.reset_results((found("Original"),))
    model.edit_query(0, "Edited")
    replacement = found("Edited", identifier="new")

    model.set_result(0, replacement)

    assert model.results == [replacement]
    assert model.selected_count == 1


def test_bulk_selection_never_approves_missing_or_error_results() -> None:
    model = ReviewListModel()
    model.reset_results(
        (
            found("Found"),
            SearchResult(query="Missing", status=SearchStatus.NO_RESULT),
            SearchResult(query="Error", status=SearchStatus.ERROR, error="offline"),
        )
    )
    model.clear_selection()
    model.select_all_found()

    approved, rows = model.selected_results()

    assert [result.query for result in approved] == ["Found"]
    assert rows == [0]


def test_waiting_and_download_status_are_presentation_only() -> None:
    model = ReviewListModel()
    model.reset_waiting(("One", "Two"))
    assert model.data(model.index(0), model.StatusRole) == "Aguardando pesquisa"

    result = found("One")
    model.set_result(0, result)
    model.set_status(0, "Baixando", "25%")

    assert model.results[0] == result
    assert model.data(model.index(0), model.StatusRole) == "Baixando"
    assert model.data(model.index(0), model.ProgressRole) == "25%"


def test_accessible_text_and_duration_are_human_readable() -> None:
    model = ReviewListModel()
    model.reset_results((found("One"),))

    accessible = model.data(model.index(0), Qt.ItemDataRole.AccessibleTextRole)

    assert "Title One" in accessible
    assert "Channel" in accessible
    assert "2:05" in accessible
    assert "selecionada" in accessible
    assert format_duration(None) == "—"
