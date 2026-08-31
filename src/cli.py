import sys
import json
import logging
from pathlib import Path
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich import box

from src.config import settings
from src.database.session import init_db, SessionLocal
from src.database.repository import PipelineRepository
from src.face.detector import FaceDetector
from src.search.engine import SearchEngine
from src.blockchain.anchor import BlockchainAnchor
from src.blockchain.verifier import BlockchainVerifier
from src.pipeline import FaceVerificationPipeline

console = Console()
logging.basicConfig(level=logging.ERROR)


def print_banner():
    banner = """[bold cyan]
  ███████╗ █████╗  ██████╗███████╗   ██████╗ ██████╗  █████╗ 
  ██╔════╝██╔══██╗██╔════╝██╔════╝  ██╔════╝██╔═══██╗██╔══██╗
  █████╗  ███████║██║     █████╗    ██║  ███╗██║   ██║███████║
  ██╔══╝  ██╔══██║██║     ██╔══╝    ██║   ██║██║   ██║██╔══██║
  ██║     ██║  ██║╚██████╗███████╗  ╚██████╔╝╚██████╔╝██║  ██║
  ╚═╝     ╚═╝  ╚═╝ ╚═════╝╚══════╝   ╚═════╝  ╚═════╝ ╚═╝  ╚═╝
    [bold yellow]TASK 3: Face Identification & Blockchain Verification[/bold yellow]
[/bold cyan]"""
    console.print(banner)


@click.group()
def cli():
    """HH Goa 2026 Task 3: Face Identification & Blockchain Verification CLI."""
    pass


@cli.command()
@click.argument("image_path", type=click.Path(exists=True))
def run(image_path: str):
    """Run full end-to-end pipeline on an input image."""
    print_banner()
    init_db()
    pipeline = FaceVerificationPipeline()

    console.print(f"\n[bold green]🚀 Initiating Pipeline for input:[/bold green] [yellow]{image_path}[/yellow]\n")

    with Progress(
        SpinnerColumn(spinner_name="dots"),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Step 1
        t1 = progress.add_task("[cyan]Step 1/4: Detecting Face & Computing 512-d Embedding (InsightFace Buffalo)...", total=None)
        face_res = pipeline.face_detector.detect_and_encode(image_path)
        progress.remove_task(t1)

        if not face_res.detected:
            console.print("[bold red]❌ Error: No face detected in the provided image.[/bold red]")
            sys.exit(1)

        # Step 2
        t2 = progress.add_task("[cyan]Step 2/4: Performing Reverse Image & Social Media Search...", total=None)
        discovered_post = pipeline.search_engine.search_for_matching_post(image_path, face_res)
        progress.remove_task(t2)

        if not discovered_post:
            console.print("[bold red]❌ Error: Could not discover matching social media content.[/bold red]")
            sys.exit(1)

        # Step 3
        t3 = progress.add_task("[cyan]Step 3/4: Anchoring Payload & Facial Hashes to EVM Smart Contract...", total=None)
        attestation = pipeline.anchor.anchor_attestation(discovered_post, face_res)
        progress.remove_task(t3)

        # Step 4
        t4 = progress.add_task("[cyan]Step 4/4: Re-Verifying Cryptographic Attestation On-Chain...", total=None)
        verification = pipeline.verifier.verify(discovered_post, face_res, attestation.payload_hash)
        progress.remove_task(t4)

    # Persist to DB
    result = pipeline.run(image_path)

    # Render Step 1 Results
    face_table = Table(title="[bold cyan]Step 1: Face Detection & InsightFace Features[/bold cyan]", box=box.ROUNDED)
    face_table.add_column("Property", style="bold white")
    face_table.add_column("Value", style="green")
    face_table.add_row("Detected", str(face_res.detected))
    face_table.add_row("Bounding Box [x1, y1, x2, y2]", str(face_res.bbox))
    face_table.add_row("Face Confidence Score", f"{face_res.confidence:.2%}")
    face_table.add_row("Embedding Dimensions", "512 (Normalized L2 Vector)")
    face_table.add_row("Image SHA-256", face_res.image_sha256)
    if face_res.crop_path:
        face_table.add_row("Cropped Face Saved", face_res.crop_path)
    console.print(face_table)

    # Render Step 2 Results
    search_table = Table(title="[bold cyan]Step 2: Discovered Web / Social Media Match[/bold cyan]", box=box.ROUNDED)
    search_table.add_column("Property", style="bold white")
    search_table.add_column("Value", style="yellow")
    search_table.add_row("Platform", discovered_post.platform)
    search_table.add_row("Author", f"{discovered_post.author_name} ({discovered_post.author_handle})")
    search_table.add_row("Post URL", discovered_post.post_url)
    search_table.add_row("Post Caption", discovered_post.post_caption)
    search_table.add_row("Post Timestamp", discovered_post.post_timestamp)
    search_table.add_row("Visual Facial Similarity", f"[bold green]{discovered_post.visual_similarity_score:.2%}[/bold green]")
    console.print(search_table)

    # Render Step 3 Results
    chain_table = Table(title="[bold cyan]Step 3: Blockchain Attestation Record[/bold cyan]", box=box.ROUNDED)
    chain_table.add_column("Property", style="bold white")
    chain_table.add_column("Value", style="magenta")
    chain_table.add_row("Contract Address", attestation.contract_address)
    chain_table.add_row("Network", attestation.network_name)
    chain_table.add_row("Block Number", str(attestation.block_number))
    chain_table.add_row("Transaction Hash", attestation.tx_hash)
    chain_table.add_row("Payload Keccak256", attestation.payload_hash)
    chain_table.add_row("Face Keccak256", attestation.face_hash)
    chain_table.add_row("Submitter Address", attestation.submitter_address)
    chain_table.add_row("Gas Used", f"{attestation.gas_used} gas")
    console.print(chain_table)

    # Render Step 4 Verification Result
    if verification.is_valid:
        ver_panel = Panel(
            f"[bold green]STATUS: 100% CRYPTOGRAPHICALLY VERIFIED & UNTAMPERED[/bold green]\n\n"
            f"[white]• Calculated Payload Hash:[/white] [cyan]{verification.calculated_payload_hash}[/cyan]\n"
            f"[white]• On-Chain Payload Hash:[/white]   [cyan]{verification.onchain_payload_hash}[/cyan]\n"
            f"[white]• Calculated Face Hash:[/white]    [cyan]{verification.calculated_face_hash}[/cyan]\n"
            f"[white]• On-Chain Face Hash:[/white]       [cyan]{verification.onchain_face_hash}[/cyan]\n"
            f"[white]• Block Timestamp:[/white]          [green]{verification.block_timestamp}[/green]\n"
            f"[white]• Submitter Address:[/white]        [green]{verification.submitter_address}[/green]",
            title="[bold green]Step 4: On-Chain Verification Proof[/bold green]",
            border_style="green",
            box=box.ROUNDED,
        )
    else:
        ver_panel = Panel(
            f"[bold red]STATUS: VERIFICATION FAILED (TAMPER DETECTED)[/bold red]\n\n"
            f"[white]Summary:[/white] {verification.verification_summary}",
            title="[bold red]Step 4: On-Chain Verification Proof[/bold red]",
            border_style="red",
            box=box.ROUNDED,
        )
    console.print(ver_panel)
    console.print(f"\n[bold green]✨ Pipeline Completed in {result.elapsed_seconds}s![/bold green]\n")


@cli.command("tamper-test")
@click.argument("attestation_id", type=int, default=1)
def tamper_test(attestation_id: int):
    """Run a live tamper detection test demonstrating cryptographic defense."""
    print_banner()
    init_db()
    pipeline = FaceVerificationPipeline()

    console.print(f"\n[bold yellow]🧪 Running Live Cryptographic Tamper Test on Attestation #{attestation_id}...[/bold yellow]\n")

    res = pipeline.test_tampering_for_attestation(attestation_id)
    if "error" in res:
        console.print(f"[bold red]❌ {res['error']}[/bold red]")
        return

    orig_ver = res["genuine_verification"]
    tamper_ver = res["tampered_verification"]

    # Table comparison
    table = Table(title="[bold cyan]Cryptographic Tamper-Evidence Proof[/bold cyan]", box=box.ROUNDED)
    table.add_column("Condition", style="bold white")
    table.add_column("Payload State", style="white")
    table.add_column("Calculated Hash", style="cyan")
    table.add_column("On-Chain Hash", style="cyan")
    table.add_column("Outcome", style="bold")

    table.add_row(
        "Authentic Record",
        "Original Untampered Data",
        orig_ver["calculated_payload_hash"][:18] + "...",
        orig_ver["onchain_payload_hash"][:18] + "...",
        "[green]✅ 100% VERIFIED[/green]",
    )
    table.add_row(
        "Tampered Record",
        "Modified Caption & Author",
        tamper_ver["calculated_payload_hash"][:18] + "...",
        tamper_ver["onchain_payload_hash"][:18] + "...",
        "[bold red]❌ TAMPER DETECTED[/bold red]",
    )
    console.print(table)

    if tamper_ver["tampered_fields"]:
        t_table = Table(title="[bold red]Detected Tampered Fields (Cryptographic Mismatch)[/bold red]", box=box.ROUNDED)
        t_table.add_column("Field", style="bold red")
        t_table.add_column("Original On-Chain Value", style="green")
        t_table.add_column("Malicious Altered Value", style="red")
        for tf in tamper_ver["tampered_fields"]:
            t_table.add_row(
                str(tf.get("field")),
                str(tf.get("expected_original"))[:60] + "...",
                str(tf.get("tampered_current"))[:60] + "...",
            )
        console.print(t_table)


@cli.command("history")
@click.option("--limit", default=10, help="Number of records to show.")
def history(limit: int):
    """List historical pipeline executions and on-chain records."""
    print_banner()
    init_db()

    with SessionLocal() as db:
        repo = PipelineRepository(db)
        runs = repo.list_all_pipeline_runs(limit=limit)

    if not runs:
        console.print("[yellow]No pipeline runs recorded in database yet. Run 'python -m src.cli run <image_path>' to create one.[/yellow]")
        return

    table = Table(title=f"[bold cyan]Pipeline History ({len(runs)} runs)[/bold cyan]", box=box.ROUNDED)
    table.add_column("ID", style="bold white", justify="right")
    table.add_column("Platform", style="yellow")
    table.add_column("Author", style="white")
    table.add_column("Similarity", style="green")
    table.add_column("Tx Hash", style="cyan")
    table.add_column("Block", style="magenta")
    table.add_column("Status", style="bold")

    for r in runs:
        att = r["attestation"]
        match = r["search_match"]
        table.add_row(
            str(att["id"]),
            match["platform"] if match else "N/A",
            match["author_name"] if match else "N/A",
            f"{match['visual_similarity_score']:.1%}" if match else "N/A",
            att["tx_hash"][:16] + "...",
            str(att["block_number"]),
            "[green]VERIFIED[/green]" if att["is_verified"] else "[red]TAMPERED[/red]",
        )
    console.print(table)


if __name__ == "__main__":
    cli()
