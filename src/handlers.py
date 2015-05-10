import logging
import middleware


@middleware.unsafe()
def regular_badge(device_id, achievement_id, config, db):
    logging.debug("regular_badge @ {}/{}".format(device_id, achievement_id))
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


# Handler dispatch:
@middleware.unsafe()
def dispatch(handlers, device_id, achievement_id, config, db):
    return handlers[config.get("handler")](device_id, achievement_id, config, db)

achievement_handlers = {
    "regular": regular_badge
}

def dispatch_achievement(device_id, achievement_id, config, db):
    return dispatch(achievement_handlers, device_id, achievement_id, config, db)


ranking_handlers = {}

def dispatch_ranking(device_id, achievement_id, config, db):
    return dispatch(ranking_handlers, device_id, achievement_id, config, db)
