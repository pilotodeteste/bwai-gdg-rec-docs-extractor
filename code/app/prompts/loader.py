from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]

PROMPT_PATHS = {
    "standard_nota_prompt": "code/app/prompts/standard_nota_prompt.txt",
    "standard_fatura_prompt": "code/app/prompts/standard_fatura_prompt.txt",
    "standard_comprovante_bancario_prompt": "code/app/prompts/standard_comprovante_bancario_prompt.txt",
}


def load_prompt(prompt_name: str) -> str:
    prompt_relative_path = PROMPT_PATHS.get(prompt_name)

    if prompt_relative_path is None:
        available = ", ".join(sorted(PROMPT_PATHS.keys()))
        raise ValueError(f"Prompt inválido: {prompt_name}. Disponíveis: {available}")

    # Caminho principal exigido no projeto.
    prompt_file = PROJECT_ROOT / prompt_relative_path
    if prompt_file.exists():
        return prompt_file.read_text(encoding="utf-8")

    # Fallback quando o processo está em outro clone/worktree.
    cwd_candidate = Path(prompt_relative_path).resolve()
    if cwd_candidate.exists():
        return cwd_candidate.read_text(encoding="utf-8")

    # Fallback quando os .txt estão ao lado do loader.
    sibling_candidate = Path(__file__).resolve().parent / Path(prompt_relative_path).name
    if sibling_candidate.exists():
        return sibling_candidate.read_text(encoding="utf-8")

    if not prompt_file.exists():
        raise FileNotFoundError(
            "Prompt não encontrado. Tentativas: "
            f"{prompt_file}, {cwd_candidate}, {sibling_candidate}"
        )


def get_standard_nota_prompt() -> str:
    return load_prompt("standard_nota_prompt")


def get_standard_fatura_prompt() -> str:
    return load_prompt("standard_fatura_prompt")


def get_standard_comprovante_bancario_prompt() -> str:
    return load_prompt("standard_comprovante_bancario_prompt")
