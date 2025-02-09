def test_case_generate(pattern:str, total_ep:int):
    return [pattern.format(ep) for ep in range(1, total_ep+1)]