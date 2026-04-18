try:
    import triton
    if not hasattr(triton, "set_allocator"):
        triton.set_allocator = lambda fn: None
except Exception:
    pass

