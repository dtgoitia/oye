import nanoid


def generate_id(prefix: str) -> str:
    short_uid = nanoid.generate(
        alphabet="abcdefghijklmnopqrstuvwxz",
        size=10,
    )
    return f"{prefix}_{short_uid}"
