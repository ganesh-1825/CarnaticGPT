def expand_query(query):
    mapping = {
        "shruti": "pitch frequency note Carnatic music",
        "gamaka": "ornamentation musical embellishment",
        "jeeva swara": "important defining swara",
        "talam": "rhythm cycle"
    }
    lower = query.lower()
    for k, v in mapping.items():
        if k in lower:
            query = query + " " + v
    return query
