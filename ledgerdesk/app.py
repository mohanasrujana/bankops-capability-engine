from pathlib import Path
from typing import Annotated, Literal

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from ledgerdesk.domain import format_usd, lookup_member, lookup_member_record

_TEMPLATE_DIRECTORY = Path(__file__).parent / "templates"
_TEMPLATES = Jinja2Templates(directory=_TEMPLATE_DIRECTORY)


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    application: str = "LedgerDesk"


def create_app() -> FastAPI:
    app = FastAPI(
        title="LedgerDesk",
        version="0.1.0",
        description="Synthetic legacy banking surface for BankOps Capability Engine",
    )

    @app.get("/", response_class=HTMLResponse)
    def member_search_page(request: Request) -> Response:
        return _TEMPLATES.TemplateResponse(
            request=request,
            name="member_search.html",
            context={"application_name": "LedgerDesk"},
        )

    @app.post("/members/search", response_class=HTMLResponse)
    def search_member(
        request: Request,
        member_id: Annotated[str, Form()],
    ) -> Response:
        result = lookup_member(member_id)
        status_code = 400 if result.status == "invalid_input" else 200

        return _TEMPLATES.TemplateResponse(
            request=request,
            name="member_search_result.html",
            context={
                "application_name": "LedgerDesk",
                "result": result,
            },
            status_code=status_code,
        )

    @app.get("/members/{record_id}", response_class=HTMLResponse)
    def member_detail(request: Request, record_id: str) -> Response:
        member = lookup_member_record(record_id)

        if member is None:
            return _TEMPLATES.TemplateResponse(
                request=request,
                name="member_record_not_found.html",
                context={"application_name": "LedgerDesk"},
                status_code=404,
            )

        return _TEMPLATES.TemplateResponse(
            request=request,
            name="member_detail.html",
            context={
                "application_name": "LedgerDesk",
                "member": member,
                "formatted_savings_balance": format_usd(member.savings_balance_cents),
            },
        )

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse()

    return app


app = create_app()
