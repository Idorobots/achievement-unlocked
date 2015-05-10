import middleware


@middleware.unsafe()
def regular_badge_for(db, achievement, device_id):
    badge = None
    template = "(SELECT count(*) FROM {table} WHERE device_id=%(device_id)s)"
    sub_queries = [template.format(table=table) for table in achievement.tables]
    query = "SELECT " + " + ".join(sub_queries) + " AS 'result';"

    db.execute(query, {'device_id': device_id})

    count = db.fetchone()['result']
    thresholds = achievement.thresholds
    badges = achievement.badges

    if count > 0:
        prev_threshold = 0
        for (idx, threshold) in enumerate(thresholds):
            if prev_threshold < count <= threshold:
                badge = badges[idx]
                break
        if count >= thresholds[-1]:
            badge = badges[-1]
    return badge
