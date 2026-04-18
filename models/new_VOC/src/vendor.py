import os
import sys
from pathlib import Path


def _has_installed_mamba_ssm() -> bool:
    try:
        import mamba_ssm  # noqa: F401
    except Exception:
        return False
    return True


def ensure_mamba_ssm_importable() -> Path:
    # Prefer the officially installed CUDA-capable mamba_ssm package.
    if _has_installed_mamba_ssm():
        return Path("<site-packages>/mamba_ssm")

    env_path = os.getenv("MAMBA_SSM_PATH")
    candidates = []
    if env_path:
        candidates.append(Path(env_path))
    src_dir = Path(__file__).resolve().parent
    project_root = src_dir.parent
    competition_root = project_root.parent
    workspace_root = competition_root.parent

    # Support both development and packaged layouts.
    candidates.extend(
        [
            project_root / "third_party" / "state-spaces-mamba",
            competition_root / "third_party" / "state-spaces-mamba",
            workspace_root / "third_party" / "state-spaces-mamba",
        ]
    )

    for candidate in candidates:
        if candidate.exists():
            candidate_str = str(candidate)
            if candidate_str not in sys.path:
                sys.path.insert(0, candidate_str)
            return candidate

    raise FileNotFoundError(
        "Unable to import official mamba_ssm. Install mamba-ssm + causal-conv1d "
        "(CUDA build) or set MAMBA_SSM_PATH to a state-spaces-mamba checkout."
    )
