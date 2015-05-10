import logging
import middleware


@middleware.unsafe()
def count_based_badge(device_id, achievement_id, config, db):
    logging.debug("count_based_badge @ {}/{}".format(device_id, achievement_id))
    badge = None
    template = "(SELECT count(*) FROM {table} WHERE device_id=%(device_id)s)"
    sub_queries = [template.format(table=table) for table in config.tables]
    query = "SELECT " + " + ".join(sub_queries) + " AS 'result';"

    db.execute(query, {'device_id': device_id})

    count = db.fetchone()['result']
    thresholds = config.thresholds
    badges = config.badges

    if count > 0:
        prev_threshold = 0
        for (idx, threshold) in enumerate(thresholds):
            if prev_threshold < count <= threshold:
                badge = badges[idx]
                break
        if count >= thresholds[-1]:
            badge = badges[-1]
    return badge


@middleware.unsafe()
def count_based_place(device_id, achievement_id, config, db):
    logging.debug("count_based_place @ {}/{}".format(device_id, achievement_id))

    def merge(x, y):
        for (k, v) in y.items():
            if k in x:
                x[k] = x[k] + v
            else:
                x[k] = v
        return x

    def index_of(m, key):
        for i, k in enumerate(sorted(m, key = lambda k: m[k])):
            if k == key:
                return i
        return None

    ranking = {}
    for table in config.tables:
        db.execute("SELECT device_id, count(*) AS 'count' FROM {} GROUP BY device_id;".format(table))
        counts = {record["device_id"]: record["count"] for record in db.fetchall()} # Might need a cursor
        ranking = merge(ranking, counts)

    return {"rank": index_of(ranking, device_id),
            "count": ranking[device_id]}


# Handler dispatch:
@middleware.unsafe()
def dispatch(handlers, device_id, achievement_id, config, db):
    return handlers[config.get("handler")](device_id, achievement_id, config, db)

achievement_handlers = {
    "count_based": count_based_badge
}

def dispatch_achievement(device_id, achievement_id, config, db):
    return dispatch(achievement_handlers, device_id, achievement_id, config, db)


ranking_handlers = {
    "count_based": count_based_place
}

def dispatch_ranking(device_id, achievement_id, config, db):
    return dispatch(ranking_handlers, device_id, achievement_id, config, db)
