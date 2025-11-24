from AGL import create_agl_instance


def main():
    agl = create_agl_instance(config=None)
    reg = getattr(agl, "integration_registry", None)
    print("Registry:", type(reg).__name__ if reg else None)
    if reg:
        try:
            keys = sorted(reg.keys())
        except Exception:
            # backwards compat
            keys = []
        print("Registered keys:", keys)

    if hasattr(agl, "process_complex_problem"):
        out = agl.process_complex_problem("ping: summarize AGL state")
        print("Process output (truncated):", str(out)[:200])


if __name__ == "__main__":
    main()
