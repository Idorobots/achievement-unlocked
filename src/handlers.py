import datetime
import easydict
import logging
import middleware
import time


@middleware.unsafe()
def count_based_badge(achievement_id, config, db, params):
    logging.debug("count_based_badge @ {}/{}".format(params.device_id, achievement_id))
    query = get_count_query(config.tables, "%(device_id)s") + ";"
    return query_based_badge(query, config, db, params)


@middleware.unsafe()
def proc_based_badge(achievement_id, config, db, params):
    logging.debug("proc_based_badge @ {}/{}".format(params.device_id, achievement_id))
    numerator = get_count_query(config.tables, "%(device_id)s")
    denominator = get_count_query(config.tables, None)
    # Achievement unlocked: Triple nested SELECT
    query = "SELECT {} / {} AS 'result';".format(numerator, denominator)
    return query_based_badge(query, config, db, params)


@middleware.unsafe()
def wifi_security_special_badge(achievement_id, config, db, params):
    logging.debug("wifi_security_special_badge @ {}/{}".format(params.device_id, achievement_id))
    query = "SELECT DISTINCT ssid FROM {} WHERE device_id = %(device_id)s;"
    db.execute(query.format(config.ssid_table), {"device_id": params.device_id})
    ssids = ",".join(["'{}'".format(s["ssid"]) for s in db.fetchall()])

    data = config.data_table
    numerator = ("(SELECT count(*) FROM {} "
                 "WHERE device_id = %(device_id)s "
                 "AND ssid IN ({}) "
                 "AND security NOT LIKE '%%WPA%%')").format(data, ssids)
    denominator = ("(SELECT count(*) FROM {} "
                   "WHERE device_id = %(device_id)s "
                   "AND ssid IN ({}))").format(data, ssids)
    query = "SELECT 1 - {} / {} AS 'result';".format(numerator, denominator)
    return query_based_badge(query, config, db, params)


@middleware.unsafe()
def wifi_funny_special_badge(achievement_id, config, db, params):
    logging.debug("wifi_funny_special_badge @ {}/{}".format(params.device_id, achievement_id))
    template = ("(SELECT count(*) FROM {} "
                "WHERE device_id = %(device_id)s "
                "AND ssid LIKE '%%{}%%')")
    sub_queries = {k: template.format(config.table, k) for (k, _) in config.badges.items()}
    sub_queries = ["{} AS '{}'".format(s, k) for k, s in sub_queries.items()]
    query = "SELECT " + ", ".join(sub_queries) + ";"
    db.execute(query, {'device_id': params.device_id})
    return [{"badge": config.badges[k],
             "value": k}
            for k, c in db.fetchone().items()
            if c > 0]


@middleware.unsafe()
def network_percent_data_badge(achievement_id, config, db, params):
    logging.debug("network_count_data_badge @ {}/{}".format(params.device_id, achievement_id))
    query = ("SELECT sum(double_received_bytes) as data_received, sum(double_sent_bytes) as data_sent "
             "FROM {} WHERE device_id = %(device_id)s".format(config.table))
    db.execute(query + ";", {'device_id': params.device_id})
    row = db.fetchone()
    data_received = row['data_received']
    data_sent = row['data_sent']
    data_total = data_received + data_sent
    result = None
    if data_sent >= data_total * config.thresholds.sender:
        result = {"badge": config.badges.sender,
                  "ratio": data_sent / data_total,
                  "threshold": config.thresholds.sender}
    elif data_received >= data_total * config.thresholds.receiver:
        result = {"badge": config.badges.receiver,
                  "ratio": data_received / data_total,
                  "threshold": config.thresholds.receiver}
    return result


# Generic *_based_badge handler.
def query_based_badge(query, config, db, params):
    db.execute(query, {'device_id': params.device_id})
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
            "value": count,
            "next_badge_at": next_badge_at}


def get_count_query(tables, device_id):
    template = "SELECT count(*) FROM {table}"

    if device_id:
        template = template + " WHERE device_id = {}".format(device_id)

    sub_queries = ["(" + template.format(table=table) + ")" for table in tables]
    return "(SELECT " + " + ".join(sub_queries) + " AS 'result')"


@middleware.unsafe()
def time_based_badge(achievement_id, config, db, params):
    logging.debug("time_based_badge @ {}/{}".format(params.device_id, achievement_id))

    query = get_time_query(config.tables, "%(device_id)s") + ";"
    db.execute(query, {'device_id': params.device_id})
    timestamp = db.fetchone()['timestamp'] / 1000  # It's a kind of magic
    now = datetime.datetime.now()  # TODO now() or utcnow()
    timedelta = now - datetime.datetime.fromtimestamp(timestamp)  # TODO fromtimestamp(t) or fromutctimestamp(t)

    thresholds = config.thresholds
    badges = config.badges

    for (b, t) in zip(badges, thresholds):
        if timedelta >= t:
            badge = b
        else:
            next_badge_at = (now - timedelta + t).timestamp()
            break

    if timedelta >= thresholds[-1]:
        next_badge_at = None

    return {"badge": badge,
            "value": timestamp,
            "next_badge_at": next_badge_at}


def get_time_query(tables, device_id):
    template = "SELECT timestamp FROM {table}"

    if device_id:
        template = template + " WHERE device_id={}".format(device_id)

    template = template + " ORDER BY timestamp ASC LIMIT 1"
    sub_queries = ["(" + template.format(table=table) + ")" for table in tables]

    return "SELECT min(timestamp) as timestamp from (" + " UNION ALL ".join(sub_queries) + ") as t"


@middleware.unsafe()
def count_based_place(achievement_id, config, db, params):
    device_id = params.device_id
    logging.debug("count_based_place @ {}/{}".format(device_id, achievement_id))
    return index_of(count_based_ranking(achievement_id, config, db, params), device_id)


@middleware.unsafe()
def proc_based_place(achievement_id, config, db, params):
    device_id = params.device_id
    logging.debug("proc_based_place @ {}/{}".format(device_id, achievement_id))
    return index_of(proc_based_ranking(achievement_id, config, db, params), device_id)


@middleware.unsafe()
def time_based_place(achievement_id, config, db, params):
    device_id = params.device_id
    logging.debug("time_based_place @ {}/{}".format(device_id, achievement_id))
    return index_of(time_based_ranking(achievement_id, config, db, params), device_id)


def index_of(l, key):
    for i, u in enumerate(l):
        if u["device_id"] == key:
            u["rank"] = i
            return u
    return None


@middleware.unsafe()
def count_based_ranking(achievement_id, config, db, params):
    logging.debug("count_based_ranking @ {}".format(achievement_id))
    return get_counts(db, config.tables, params)


@middleware.unsafe()
def proc_based_ranking(achievement_id, config, db, params):
    logging.debug("proc_based_ranking @ {}".format(achievement_id))
    counts = get_counts(db, config.tables, params)
    sum = 0
    for c in counts:
        sum += c["value"]

    for c in counts:
        c["value"] = c["value"] / sum

    return counts


def get_counts(db, tables, params):
    def merge(x, y):
        for (k, v) in y.items():
            if k in x:
                x[k] = x[k] + v
            else:
                x[k] = v
        return x

    query = ("SELECT device_id, count(*) AS 'value' FROM {} "
             "WHERE timestamp >= %(from)s AND timestamp <= %(to)s "
             "GROUP BY device_id;")

    ranking = {}
    for table in tables:
        db.execute(query.format(table), build_time_range(params["from"], params["to"]))
        counts = {record["device_id"]: record["value"] for record in db.fetchall()} # Might need a cursor
        ranking = merge(ranking, counts)

    keys = sorted(ranking, key=lambda k: ranking[k], reverse=True)
    return [{"device_id": k, "value": ranking[k]} for k in keys]


@middleware.unsafe()
def time_based_ranking(achievement_id, config, db, params):
    def dict_for(d, device_id):
        return {"device_id": device_id,
                "value": d[device_id]}

    logging.debug("time_based_ranking @ {}".format(achievement_id))

    tables = config.tables

    template = "SELECT device_id, min(timestamp) as timestamp FROM {} GROUP BY device_id"
    subqueries = "UNION ALL ".join(["(" + template.format(table) + ")" for table in tables])
    query = "SELECT device_id, min(timestamp) as timestamp FROM (" + subqueries + ") as t GROUP BY device_id"
    db.execute(query)
    d = {record["device_id"]: record["timestamp"] for record in db.fetchall()}

    return [dict_for(d, device_id) for device_id in sorted(d, key=lambda k: d[k])]


def build_time_range(frm, to):
    return {"from": frm or "0",
            "to": to or str(int(time.time()) * 1000)} # NOTE Aware stores timestamps in unixtime millis


# Handler dispatch:
@middleware.unsafe()
def dispatch(handlers, config, achievement_id, db, params={}):
    return {k: handlers[h](achievement_id, c, db, easydict.EasyDict(params)) for k, (h, c) in config.items()}


# Handler initialization
ranking_handlers = {
    "count_based": count_based_ranking,
    "procent_based": proc_based_ranking,
    "time_based": time_based_ranking
}

user_achievement_handlers = {
    "count_based": count_based_badge,
    "procent_based": proc_based_badge,
    "time_based":  time_based_badge,
    "wifi_security_special": wifi_security_special_badge,
    "wifi_funny_special": wifi_funny_special_badge,
    "network_percent_data": network_percent_data_badge
}

user_ranking_handlers = {
    "count_based": count_based_place,
    "procent_based": proc_based_place,
    "time_based": time_based_place
}


handlers = easydict.EasyDict({})
handlers.ranking = ranking_handlers
handlers.user = {}
handlers.user.achievements = user_achievement_handlers
handlers.user.ranking = user_ranking_handlers
