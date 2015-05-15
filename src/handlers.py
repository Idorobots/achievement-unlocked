import easydict
import logging
import middleware


@middleware.unsafe()
def count_based_badge(achievement_id, config, db, params):
    device_id = params.device_id
    logging.debug("count_based_badge @ {}/{}".format(device_id, achievement_id))

    config = config.count  # FIXME

    template = "(SELECT count(*) FROM {table} WHERE device_id=%(device_id)s)"
    sub_queries = [template.format(table=table) for table in config.tables]
    query = "SELECT " + " + ".join(sub_queries) + " AS 'result';"

    db.execute(query, {'device_id': device_id})

    count = db.fetchone()['result']
    thresholds = config.thresholds
    badges = config.badges

    badge = None
    next_badge_at = thresholds[0]

    for (b, t) in zip(badges, thresholds):
        if count >= t:
            badge = b
        else:
            next_badge_at = t
            break

    if count >= thresholds[-1]:
        next_badge_at = None

    return {"badge": badge,
            "count": count,
            "next_badge_at": next_badge_at}


@middleware.unsafe()
def count_based_place(achievement_id, config, db, params):
    device_id = params.device_id
    logging.debug("count_based_place @ {}/{}".format(device_id, achievement_id))

    def index_of(l, key):
        for i, u in enumerate(l):
            if u["device_id"] == key:
                u["rank"] = i
                return u
        return None

    return index_of(count_based_ranking(achievement_id, config, db, params), device_id)


@middleware.unsafe()
def count_based_ranking(achievement_id, config, db, params):
    logging.debug("count_based_ranking @ {}".format(achievement_id))

    config = config.count  # FIXME

    def merge(x, y):
        for (k, v) in y.items():
            if k in x:
                x[k] = x[k] + v
            else:
                x[k] = v
        return x

    ranking = {}
    for table in config.tables:
        db.execute("SELECT device_id, count(*) AS 'count' FROM {} GROUP BY device_id;".format(table))
        counts = {record["device_id"]: record["count"] for record in db.fetchall()} # Might need a cursor
        ranking = merge(ranking, counts)

    keys = sorted(ranking, key=lambda k: ranking[k])
    return [{"device_id": k, "count": ranking[k]} for k in keys]


# Handler dispatch:
@middleware.unsafe()
def dispatch(handlers, achievement_id, config, db, params={}):
    return handlers[config.get("handler")](achievement_id, config, db, easydict.EasyDict(params))


# Handler initialization

achievement_handlers = {
    "count_based": count_based_badge
}

ranking_handlers = {
    "count_based": count_based_ranking
}

user_achievement_handlers = {
    "count_based": count_based_badge
}

user_ranking_handlers = {
    "count_based": count_based_place
}


handlers = easydict.EasyDict({})
handlers.achievements = achievement_handlers
handlers.ranking = ranking_handlers
handlers.user = {}
handlers.user.achievements = user_achievement_handlers
handlers.user.ranking = user_ranking_handlers
