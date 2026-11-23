"""QV-R01 local research model. Standard library only. No market data."""
from dataclasses import dataclass
from math import exp, floor, isclose
from statistics import pstdev

LAMBDA = .85
COST = .001 + .0005


def windows(period):
    minutes = {
        "1": 1, "5": 5, "15": 15, "30": 30, "60": 60, "1h": 60,
        "120": 120, "2h": 120, "240": 240, "4h": 240, "D": 1440,
        "1D": 1440, "W": 10080, "1W": 10080, "M": 43200, "1M": 43200,
    }.get(period, 60)
    if minutes >= 1440:
        return minutes, 3, 6, max(8, floor(2160 / minutes + .5))
    return (minutes, max(5, floor(1440 / minutes + .5)),
            max(10, floor(2880 / minutes + .5)), max(8, floor(2160 / minutes + .5)))


def clip(value):
    return max(0., min(1., value))


def decision(actions, weights, raw_p1, variant="original"):
    supports = tuple(sum(w for a, w in zip(actions, weights) if a == direction)
                     for direction in (1, -1, 0))
    up, down, null = supports
    if variant == "sin_nulo":
        null = 0.
    majority = 1 if up > max(down, null) else -1 if down > max(up, null) else 0
    total = up + down + null
    ratio = max(up, down, null) / total if total > 0 else 0.
    minimum = min((w for a, w in zip(actions, weights) if a == majority),
                  default=0.) if majority else 0.
    _, p2, p3 = actions
    base = 1. if raw_p1 and raw_p1 == p3 else .7 if raw_p1 or p3 else .5
    penalty = .7 if p2 and -p2 in (raw_p1, p3) else 1.
    semantic = base * penalty
    gamma = ratio * (1. if variant == "sin_minimo" else minimum)
    gamma *= (1. if variant == "sin_alineacion" else semantic) * exp(-2 * (1 - ratio))
    final = majority if gamma >= .3 and ratio >= .6 else 0
    return supports, majority, ratio, minimum, semantic, gamma, final


def update_memory(memory, previous, previous_context, realized, eligible):
    updated = [row.copy() for row in memory]
    if eligible:
        for row, action in zip(updated, previous):
            if action:
                old = row[previous_context]
                row[previous_context] = LAMBDA * old + (1 - LAMBDA) * (action * realized - COST > 0)
    return updated


@dataclass(frozen=True)
class Level:
    price: float | None = None
    remaining: int = 0

    def step(self, creation, present, lag5):
        price = creation if creation is not None else self.price
        remaining = 20 if creation is not None else self.remaining
        remaining = max(remaining - 1, 0)
        if price is not None and lag5 is not None and present < lag5 * .5:
            return Level()
        return Level(price, remaining)

    def display(self, enabled=True):
        return self.price if enabled else None


def evaluate(bars, period="60"):
    """Bars are (open, high, low, close). Model emits mature-window traces."""
    _, fast, slow, vol_window = windows(period)
    closes = [bar[3] for bar in bars]
    assert all(0 < low <= min(op, close) <= max(op, close) <= high
               for op, high, low, close in bars)
    memory = [[.5] * 4 for _ in range(3)]
    previous, previous_context = (0, 0, 0), 2
    previous_final = 0
    levels = (Level(), Level())
    ema_fast = ema_slow = None
    true_ranges, atrs, trace = [], [], []
    for t, (_, high, low, close) in enumerate(bars):
        prior = closes[t - 1] if t else close
        true_ranges.append(max(high - low, abs(high - prior), abs(low - prior)))
        if len(true_ranges) == vol_window:
            atrs.append(sum(true_ranges) / vol_window)
        elif len(true_ranges) > vol_window:
            atrs.append((atrs[-1] * (vol_window - 1) + true_ranges[-1]) / vol_window)
        else:
            atrs.append(None)
        if t:
            ema_fast = prior if ema_fast is None else ema_fast + 2 / (fast + 1) * (prior - ema_fast)
            ema_slow = prior if ema_slow is None else ema_slow + 2 / (slow + 1) * (prior - ema_slow)
        if t == 0:
            trace.append(None)
            continue
        memory = update_memory(memory, previous, previous_context, (close - prior) / prior, t > slow)
        momentum = (ema_fast > ema_slow) - (ema_fast < ema_slow)
        er = .5
        if t >= slow + 2:
            history = closes[t - slow - 1:t]
            traveled = sum(abs(a - b) for a, b in zip(history, history[1:]))
            er = abs(prior - history[0]) / traveled if traveled else 0.
        a1 = momentum if er > .6 else 0
        vol = pstdev(closes[t - vol_window:t]) / prior if t >= vol_window else None
        phi1 = clip(er * (1 - min(vol / .02, 1.))) if vol is not None else None
        if t >= slow:
            sample = closes[t - slow:t]
            sigma = pstdev(sample)
            z = (prior - sum(sample) / slow) / sigma if sigma else 0.
        else:
            z = 0.
        slow_bars = bars[max(0, t - slow):t]
        slow_low, slow_high = min(row[2] for row in slow_bars), max(row[1] for row in slow_bars)
        pos2 = (prior - slow_low) / (slow_high - slow_low) if slow_high > slow_low else .5
        a2 = 1 if z < -1.5 and pos2 < .2 else -1 if z > 1.5 and pos2 > .8 else 0
        phi2 = clip((1 - min(abs(z) / 3, 1.)) * (1 - abs(pos2 - .5) * 2))
        atr_window = atrs[max(0, t - slow):t]
        atr_ratio = atr_window[-1] / (sum(atr_window) / slow) if (
            len(atr_window) == slow and None not in atr_window and sum(atr_window) > 0
        ) else 1.
        fast_bars = bars[max(0, t - fast):t]
        fast_low, fast_high = min(row[2] for row in fast_bars), max(row[1] for row in fast_bars)
        pos3 = (prior - fast_low) / (fast_high - fast_low) if fast_high > fast_low else .5
        a3 = (1 if pos3 > .7 else -1 if pos3 < .3 else 0) if atr_ratio > 1.2 else 0
        phi3 = clip(min(atr_ratio / 1.5, 1.) * (1 - abs(pos3 - .5) * 2))
        context = 0 if a1 == 1 else 1 if a1 == -1 else 3 if vol is not None and vol > .025 else 2
        actions = a1, a2, a3
        previous, previous_context = actions, context
        if phi1 is None:
            trace.append(None)
            continue
        reliability = tuple(row[context] for row in memory)
        weights = tuple(phi * rel for phi, rel in zip((phi1, phi2, phi3), reliability))
        metrics = decision(actions, weights, momentum)
        supports, _, ratio, _, semantic, gamma, final = metrics
        transition = final if final and final != previous_final else 0
        quality = gamma * ratio * semantic if transition else 0.
        lag = trace[t - 5]["metrics"][0] if t >= 5 and trace[t - 5] is not None else (None, None)
        creation = (bars[t - 1][2] if transition == 1 and quality >= .5 else None,
                    bars[t - 1][1] if transition == -1 and quality >= .5 else None)
        levels = tuple(level.step(price, current, old)
                       for level, price, current, old in zip(levels, creation, supports, lag))
        previous_final = final
        trace.append(dict(t=t, actions=actions, weights=weights, momentum=momentum, er=er, z=z,
                          pos2=pos2, pos3=pos3, atr_ratio=atr_ratio, reliability=reliability,
                          metrics=metrics, transition=transition, quality=quality,
                          creation=creation, levels=levels, context=context,
                          memory=tuple(tuple(row) for row in memory)))
    return trace


def synthetic_bars():
    bars = []
    close = 100.
    for t in range(1000):
        close *= 1.0017
        low, high = (close * .98, close * 1.0084) if t % 60 == 0 else (close * .99995, close * 1.00005)
        bars.append((close, high, low, close))
    anchor = close * .95
    for t in range(80):
        close = anchor * (1 + .00002 * (t % 2))
        bars.append((close, close * 1.00005, close * .99995, close))
    close = anchor * 1.012
    bars.append((close, close * 1.0125, close * .97, close))
    bars.append((close, close * 1.00005, close * .99995, close))
    return bars


VOTE_CASES = (
    ("P1/P2", (1, 1, 0), (.82, .10, .03), 1, (1, 0, 1, 0, 0)),
    ("P1/P3", (1, 0, 1), (.73, .01, .55), 1, (1, 1, 1, 1, 1)),
    ("opuestos", (1, 0, -1), (.80, .01, .12), 1, (1, 1, 1, 1, 1)),
    ("empate", (1, 0, -1), (.25, .04, .25), 1, (0, 0, 0, 0, 0)),
    ("neutro_gana", (1, 0, 0), (.45, .48, .32), 1, (0, 0, 0, 1, 0)),
    ("neutro_alto", (1, 0, 0), (.10, .48, .32), 1, (0, 0, 0, 0, 0)),
    ("sin_direccion", (0, 0, 0), (.4, .5, .3), 1, (0, 0, 0, 0, 0)),
    ("masa_cero", (1, 0, -1), (0., 0., 0.), 1, (0, 0, 0, 0, 0)),
    ("alineacion_decisiva", (1, 0, 0), (.40, .01, .01), 1, (1, 0, 1, 0, 1)),
    ("solo_alineacion", (1, 0, -1), (.99, 0., .54), 1, (1, 0, 0, 0, 1)),
    ("neutral_empata", (1, 0, 0), (.48, .30, .18), 1, (0, 0, 0, 1, 0)),
)


def vote_checks():
    for name, actions, weights, momentum, expected in VOTE_CASES:
        original = decision(actions, weights, momentum)
        variants = tuple(decision(actions, weights, momentum, variant)[-1]
                         for variant in ("sin_minimo", "sin_nulo", "sin_alineacion"))
        observed = (original[1], original[-1], *variants)
        print("E1/E4", name, original, variants)
        assert observed == expected, (name, observed, expected)


def memory_checks():
    seed = [[.5] * 4 for _ in range(3)]
    assert (update_memory(seed, (1, 0, -1), 1, .03, False) == seed)
    histories = ((.002, -.002, COST), (.10, -.07, COST))
    results = []
    for returns in histories:
        state = seed
        for realized, context in zip(returns, (1, 3, 1)):
            state = update_memory(state, (1, 0, -1), context, realized, True)
            print("E2", realized, context, state)
        results.append(state)
    assert results[0] == results[1]
    expected = [[.48875, .425], [.5, .5], [.36125, .575]]
    for row, pair in zip(results[0], expected):
        assert all(isclose(row[context], value) for context, value in zip((1, 3), pair))
        assert row[0] == row[2] == .5
    revisions = [update_memory(seed, (1, 0, 0), 0, ret, True)
                 for ret in (.002, .001)]
    final = [decision((1, 0, 0), (state[0][0] * .8, 0., 0.), 1)[-1]
             for state in revisions]
    print("E2 revisiones desde el mismo estado", [state[0][0] for state in revisions], final)
    assert final == [1, 0]
    for period, expected_window in {
        "1": (1, 1440, 2880, 2160), "5": (5, 288, 576, 432),
        "15": (15, 96, 192, 144), "30": (30, 48, 96, 72),
        "60": (60, 24, 48, 36), "120": (120, 12, 24, 18),
        "240": (240, 6, 12, 9), "D": (1440, 3, 6, 8),
        "W": (10080, 3, 6, 8), "M": (43200, 3, 6, 8),
        "3": (60, 24, 48, 36), "2D": (60, 24, 48, 36),
    }.items():
        assert windows(period) == expected_window
        print("E2 ventana", period, expected_window)
    for alias, canonical in (("1h", "60"), ("2h", "120"), ("4h", "240"),
                             ("1D", "D"), ("1W", "W"), ("1M", "M")):
        assert windows(alias) == windows(canonical)
    # Daily Wslow=6 and Wvol=8. The bearish P2 vote at t=6 loses
    # on the rise at t=7, even though ER still uses its fallback.
    warmup_closes = [100.] * 5 + [101., 102., 103., 104.]
    warmup = evaluate([(c, c + .01, c - .01, c) for c in warmup_closes], "D")[8]
    assert warmup["er"] == 1. and warmup["actions"][0] == 1
    assert isclose(warmup["memory"][1][2], .5 * .85 ** 2)
    print("E2 calentamiento", warmup)


def level_checks():
    level = Level().step(100., 0., 0.)
    assert level == Level(100., 19)
    for elapsed in range(1, 21):
        level = level.step(None, 0., 0.)
        assert level.remaining == max(19 - elapsed, 0)
        assert level.display() == 100. and level.display(False) is None
    assert level.step(None, .2, .4) == level
    assert level.step(None, .199, .4) == Level()
    assert level.step(None, 0., .4) == Level()
    assert level.step(101., .3, .4) == Level(101., 19)
    assert level.step(101., .1, .4) == Level()
    assert level.step(None, 0., None) == level
    print("E3 nivel", level, "visible", level.display(), "reemplazo", level.step(101., .3, .4))


def ohlc_checks():
    bars = synthetic_bars()
    trace = evaluate(bars)
    mature = [row for row in trace[60:] if row is not None]
    for name, predicate in (
        ("P1/P3", lambda a: a[0] != 0 and a[0] == a[2]),
        ("opuestos", lambda a: -1 in a and 1 in a),
        ("sin_direccion", lambda a: a == (0, 0, 0)),
    ):
        row = next((row for row in mature if predicate(row["actions"])), None)
        assert row is not None
        print("E1 OHLC", name, row)
    closes = [100 + .1 * t for t in range(80)] + [113.] * 5 + [112.8, 113.]
    daily = evaluate([(c, c + .01, c - .01, c) for c in closes], "D")[-1]
    assert daily["actions"] == (1, 1, 0) and daily["metrics"][-1] == 0
    zero = evaluate([(100., 100., 99., 100.)] * 70)[-1]
    assert zero["metrics"] == ((0, 0, 0.), 0, 0., 0., .5, 0., 0)
    print("E1 OHLC P1/P2 diario", daily)
    print("E1 OHLC masa cero", zero)
    for name, variant in (("minimo", "sin_minimo"), ("nulo", "sin_nulo"),
                          ("alineacion", "sin_alineacion")):
        changed = [row["t"] for row in mature if
                   decision(row["actions"], row["weights"], row["momentum"], variant)[-1]
                   != row["metrics"][-1]]
        print("E4 OHLC", name, len(changed), changed[:5])
    assert all(row["quality"] <= .49 + 1e-12 for row in mature
               if not row["momentum"] or row["momentum"] != row["actions"][2])
    creations = [row for row in mature if any(price is not None for price in row["creation"])]
    assert [row["t"] for row in creations] == [1081]
    assert creations[0]["levels"][0] == Level(bars[1080][2], 19)
    print("E3 OHLC creaciones", len(creations), "dominio", len(bars))
    for row in trace[-2:]:
        print("E3 OHLC extremo", row)


if __name__ == "__main__":
    vote_checks()
    memory_checks()
    level_checks()
    ohlc_checks()
