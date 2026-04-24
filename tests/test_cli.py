from cash_recon.cli import build_parser


def test_cli_accepts_version_flag():
    parser = build_parser()
    args = parser.parse_args(["--version"])

    assert args.version is True