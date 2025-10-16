from assistant.composer.run_digest import main

def test_main_does_not_raise(capsys):
    # Main should print two lines and not raise.
    main()
    out, err = capsys.readouterr()
    assert "Daily Quant Digest" in out
    assert "Skeleton OK" in out
    assert err == ""
