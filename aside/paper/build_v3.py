"""Version 3. Same paper as version 2, plus the default scene-cut encode.

Reads clips/decisions.csv and clips/decisions_scenecut.csv. Does not encode.
"""

import csv
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLIPS = ROOT / "clips"
V2 = Path(__file__).resolve().parent / "the-page-between-the-samples-v2.html"
OUT = Path(__file__).resolve().parent / "the-page-between-the-samples-v3.html"
SEED = 20261010


def load(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def num(row, key):
    value = row.get(key, "")
    return None if value in ("", None) else float(value)


def bootstrap(values):
    rng = random.Random(SEED)
    n = len(values)
    means = []
    for _ in range(10000):
        draw = [values[rng.randrange(n)] for _ in range(n)]
        means.append(sum(draw) / n)
    means.sort()
    return sum(values) / n, means[249], means[9749]


def page_of(log_row):
    start = int(log_row["start"])
    hold = int(log_row["hold"])
    return start, start + hold


def inside(frame, start, end):
    return frame is not None and start <= frame < end


def fmt(value, digits=2):
    return f"{value:.{digits}f}"


def chosen_row(clip, crf):
    path = CLIPS / "work" / clip / "scores_b" / "summary.csv"
    for row in load(path):
        if int(row["crf"]) == int(crf):
            return row
    raise SystemExit(f"{clip} has no scene-cut-on summary row for CRF {crf}")


def main():
    off_rows = load(CLIPS / "decisions.csv")
    on_path = CLIPS / "decisions_scenecut.csv"
    if not on_path.exists():
        raise SystemExit("clips/decisions_scenecut.csv is missing")
    on_rows = load(on_path)
    if len(on_rows) != 18:
        raise SystemExit(f"scene-cut-on table has {len(on_rows)} rows, need 18")
    off = {row["clip"]: row for row in off_rows}
    on = {row["clip"]: row for row in on_rows}
    log = {row["clip"]: row for row in load(CLIPS / "log.csv")}
    comp = [f"{i:02d}" for i in range(1, 13)]
    bound = [f"{i:02d}" for i in range(13, 19)]

    def pack(ids):
        rows = []
        for clip in ids:
            a, b = off[clip], on[clip]
            start, end = page_of(log[clip])
            summary = chosen_row(clip, b["spread_crf"]) if b["spread_crf"] else None
            ninth_frame = int(b["spread_ninth_frame"]) if b["spread_ninth_frame"] else None
            forty_frame = int(summary["fortyfifth_frame"]) if summary else None
            forty = float(summary["fortyfifth"]) if summary else None
            rows.append(
                {
                    "clip": clip,
                    "off_s": num(a, "spread_shortfall"),
                    "on_s": num(b, "spread_shortfall"),
                    "off_crf": a["spread_crf"],
                    "on_crf": b["spread_crf"],
                    "off_ninth": num(a, "spread_ninth"),
                    "on_ninth": num(b, "spread_ninth"),
                    "off_set_s": num(a, "settled_shortfall"),
                    "on_set_s": num(b, "settled_shortfall"),
                    "off_set_crf": a["settled_crf"],
                    "on_set_crf": b["settled_crf"],
                    "off_bytes": int(a["spread_bytes"]),
                    "on_bytes": int(b["spread_bytes"]) if b["spread_bytes"] else None,
                    "off_set_bytes": int(a["settled_bytes"]),
                    "on_set_bytes": int(b["settled_bytes"]) if b["settled_bytes"] else None,
                    "ninth_in": inside(ninth_frame, start, end),
                    "ninth_frame": ninth_frame,
                    "forty": forty,
                    "forty_in": inside(forty_frame, start, end),
                    "start": start,
                    "end": end,
                }
            )
        return rows

    comp_rows = pack(comp)
    bound_rows = pack(bound)
    off_vals = [row["off_s"] for row in comp_rows]
    on_vals = [row["on_s"] for row in comp_rows]
    shrink = [row["off_s"] - row["on_s"] for row in comp_rows]
    off_mean, off_lo, off_hi = bootstrap(off_vals)
    on_mean, on_lo, on_hi = bootstrap(on_vals)
    sh_mean, sh_lo, sh_hi = bootstrap(shrink)
    on_sorted = sorted(on_vals)
    on_median = (on_sorted[5] + on_sorted[6]) / 2
    still = sum(1 for value in on_vals if value > 0)
    smaller = sum(1 for row in comp_rows if row["on_s"] < row["off_s"] - 1e-9)
    larger = sum(1 for row in comp_rows if row["on_s"] > row["off_s"] + 1e-9)
    settled_clear = sum(1 for row in comp_rows if row["on_set_s"] == 0)
    ninth_in = sum(1 for row in comp_rows if row["ninth_in"])
    forty_out = sum(1 for row in comp_rows if row["forty"] is not None and row["forty"] >= 90 and not row["forty_in"])
    forty_min = min(row["forty"] for row in comp_rows)
    bound_on = [row["on_s"] for row in bound_rows]
    bound_off = [row["off_s"] for row in bound_rows]
    size_ratios = [row["on_set_bytes"] / row["on_bytes"] for row in comp_rows]
    lines = []
    for row in comp_rows:
        lines.append(
            "<tr>"
            f"<td>{row['clip']}</td>"
            f"<td class='right'>{row['off_crf']}</td>"
            f"<td class='right'>{fmt(row['off_s'])}</td>"
            f"<td class='right'>{row['on_crf']}</td>"
            f"<td class='right'>{fmt(row['on_ninth'], 1)}</td>"
            f"<td class='right'>{fmt(row['on_s'])}</td>"
            f"<td class='right'>{fmt(row['off_s'] - row['on_s'])}</td>"
            f"<td class='right'>{row['on_set_crf']}</td>"
            f"<td class='right'>{fmt(row['on_set_s'])}</td>"
            f"<td>{'page' if row['ninth_in'] else 'outside'}</td>"
            "</tr>"
        )
    bound_lines = []
    for row in bound_rows:
        bound_lines.append(
            "<tr>"
            f"<td>{row['clip']}</td>"
            f"<td class='right'>{fmt(row['off_s'])}</td>"
            f"<td class='right'>{fmt(row['on_s'])}</td>"
            f"<td class='right'>{fmt(row['on_set_s'])}</td>"
            "</tr>"
        )

    # I-frames on the chosen even-frame file. Frame = round(pts_time * 30)
    # from ffmpeg -skip_frame nokey -vf showinfo. Refuse to reuse the sentence
    # if a later run picks a different CRF.
    probed = {
        "01": "38", "02": "37", "03": "38", "04": "37",
        "05": "35", "06": "37", "07": "36", "08": "37",
        "09": "38", "10": "37", "11": "35", "12": "37",
        "13": "33", "16": "37", "18": "36",
    }
    for clip, crf in probed.items():
        if on[clip]["spread_crf"] != crf:
            raise SystemExit(f"clip {clip} even CRF is {on[clip]['spread_crf']}, keyframes were read at {crf}")
    cut_i = {"01", "02", "03", "04", "06", "08", "09", "10", "11", "12"}
    keyed_miss = [row["on_s"] for row in comp_rows if row["clip"] in cut_i and row["on_s"] > 0]
    closed = [row["clip"] for row in comp_rows if row["on_s"] == 0]
    if closed != ["11"] or len(keyed_miss) != 9 or still != 11 or settled_clear != 12:
        raise SystemExit(
            f"section 6.5 prose is written for this result; got closed {closed}, "
            f"keyed misses {len(keyed_miss)}, still {still}, settled {settled_clear}"
        )
    if ninth_in != 12 or forty_out != 12:
        raise SystemExit(f"9th/45th pattern changed: ninth_in {ninth_in}, forty_out {forty_out}")
    row11 = next(row for row in comp_rows if row["clip"] == "11")
    row01 = next(row for row in comp_rows if row["clip"] == "01")
    row13 = next(row for row in bound_rows if row["clip"] == "13")
    row16 = next(row for row in bound_rows if row["clip"] == "16")
    row18 = next(row for row in bound_rows if row["clip"] == "18")
    larger_anyway = [
        row["clip"] for row in comp_rows
        if row["on_bytes"] > row["off_bytes"] and int(row["on_crf"]) >= int(row["off_crf"])
    ]
    bound_closed = sum(1 for row in bound_rows if row["on_s"] == 0)
    bound_settled_clear = sum(1 for row in bound_rows if row["on_set_s"] == 0)
    ratio_mean = sum(size_ratios) / len(size_ratios)
    close = (
        f"With scene-cut left on, the even-frame mean on these twelve clips is {on_mean:.2f} "
        f"rather than {off_mean:.2f}. The shortfall reaches zero on clip 11 only. "
        "The 9th-worst frame stays inside the page on all twelve."
    )
    if larger == 0 and smaller == 12:
        move = "The shortfall gets smaller on every clip."
    else:
        move = f"The shortfall gets smaller on {smaller} clips and larger on {larger}."

    section = f'''
  <h3>6.5 The same clips with scene-cut left on</h3>
  <p>The encodes above refuse a keyframe at the cut. This section repeats the choice with that refusal lifted. libx264 is still preset medium, yuv420p, one CRF for the file. The flags that forced a keyframe interval of 999 and a scene-cut threshold of 0 are omitted. The encoder's own option string on these files reads keyint=250, keyint_min=25, scenecut=40. Tables 1 to 3 stay as they were. Table 4 is this encode.</p>
  <p>The ladder is the same kind of ladder. It starts at CRF 28, 32, 36, 40, and 44. Integer rungs are filled until the even-frame vote and the settled vote have no gap between the highest passing CRF and the next encoded CRF above it. The other eight-frame rules read those rungs. They do not add encodes. The frame lists do not change: the same even centers, the same settled frames, the same cut, the same random draw, and the same detail frames.</p>
  <p>On clip 01 at CRF 28, the new file has I-frames at frames 0, 250, 500, 538, and 788. Frame 538 is the cut onto the page. The scene-cut-off file at CRF 28, and the scene-cut-off file at CRF 36, the rung the even rule chose, each have an I-frame only at frame 0. On the even-frame file actually chosen under the default encoder, ten of the twelve comparison clips have an I-frame on the cut into the page. Clips 05 and 07 do not. Their cuts are frames 517 and 514, which sit 17 and 14 frames after the periodic I-frame at frame 500, inside the minimum keyframe gap of 25. The scene-cut I-frame falls on the return instead, frames 537 and 534, the first frame after the page. Where the cut into the page is an I-frame, the return twenty frames later is not. It falls inside that same gap.</p>
  <p>The twelve-clip even-frame shortfall falls from {off_mean:.2f} to {on_mean:.2f}. A 10,000-draw bootstrap of the scene-cut-on shortfalls, seed 20261010, runs from {on_lo:.2f} to {on_hi:.2f}. The same draw on the scene-cut-off shortfalls runs from {off_lo:.2f} to {off_hi:.2f}. The mean reduction is {sh_mean:.2f}, with a resampling interval from {sh_lo:.2f} to {sh_hi:.2f}. The median scene-cut-on shortfall is {on_median:.2f}. {move} It reaches zero only on clip 11. There the CRF stays {row11['on_crf']}, the 9th-worst is {fmt(row11['on_ninth'], 1)}, and that frame, {row11['ninth_frame']}, is still inside the page. The settled shortfall stays zero on all twelve. An I-frame on the cut is not the same thing as meeting 90. Nine of the ten files that have one still miss, from {min(keyed_miss):.2f} to {max(keyed_miss):.2f}. Clips 05 and 07, whose I-frame lands on the return, miss by {fmt(next(row['on_s'] for row in comp_rows if row['clip']=='05'))} and {fmt(next(row['on_s'] for row in comp_rows if row['clip']=='07'))}.</p>
  <p>The 9th-worst frame of the even-frame file is still inside the 20-frame page on all twelve clips. The 45th-worst frame is outside the page on all twelve, and the lowest of those scores is {forty_min:.2f}. Scene-cut has raised the page's score. It has not moved the tail off the page. The settled rule is what still holds every comparison file at 90.</p>
  <table class="dense">
    <thead><tr>
      <th>Clip</th><th>Off CRF</th><th>Off shortfall</th><th>On CRF</th><th>On 9th</th><th>On shortfall</th><th>Shrink</th><th>Settled CRF</th><th>Settled shortfall</th><th>9th frame</th>
    </tr></thead>
    <tbody>
      {''.join(lines)}
    </tbody>
  </table>
  <p class="status" style="text-align:left;margin-top:2px">Table 4. Comparison set with scene-cut left on. Off is the scene-cut-off encode in clips/decisions.csv. On is clips/decisions_scenecut.csv. Shrink is the off shortfall minus the on shortfall. Settled columns are the scene-cut-on file. The 9th-frame cell says whether that frame of the even-frame file sits inside the page. Source: clips/decisions.csv, clips/decisions_scenecut.csv, and clips/work/&lt;clip&gt;/scores_b/summary.csv. I-frame lists were read from the chosen even-frame files.</p>
  <p>The settled file is {ratio_mean:.2f} times the even-frame file on average, from {min(size_ratios):.2f} to {max(size_ratios):.2f}. On clip 11 the two rules choose the same CRF, so the ratio is 1. On {("zero one two three four five six seven eight nine ten eleven twelve").split()[len(larger_anyway)]} clips the scene-cut-on even-frame file is larger than the scene-cut-off file at the same or a harsher CRF. Clip 01 is one of them: CRF {row01['on_crf']} is {row01['on_bytes']:,} bytes, and the scene-cut-off file at CRF {row01['off_crf']} is {row01['off_bytes']:,} bytes. The comparison that belongs in the claim is the pair encoded the same way.</p>
  <p>The six boundary clips move in the same direction. Their even-frame mean shortfall goes from {sum(bound_off)/len(bound_off):.2f} to {sum(bound_on)/len(bound_on):.2f}. {("zero one two three four five six").split()[bound_closed].capitalize()} of the six reach shortfall zero. Clip 16 does not. Its cut, frame 515, is 15 frames after the I-frame at frame 500, so the scene-cut I-frame is the return at frame 535, and the shortfall is {fmt(row16['on_s'])}. Clip 18 does have an I-frame on the cut, and its shortfall is still {fmt(row18['on_s'])}. Settled shortfall is zero on {("zero one two three four five six").split()[bound_settled_clear]} of the six. On clip 13 the settled file misses by {fmt(row13['on_set_s'])} while the even-frame file clears. Those six stay out of the twelve-clip mean.</p>
  <table>
    <thead><tr><th>Clip</th><th>Off shortfall</th><th>On shortfall</th><th>Settled shortfall</th></tr></thead>
    <tbody>{''.join(bound_lines)}</tbody>
  </table>
  <p class="status" style="text-align:left;margin-top:2px">Table 5. Boundary clips, scene-cut off against scene-cut on. Not in the twelve-clip mean.</p>
'''

    html = V2.read_text(encoding="utf-8")
    html = html.replace(
        "<title>The page between the samples</title>",
        "<title>The page between the samples, version 3</title>",
    )
    html = html.replace(
        "<h1>The page between the samples</h1>",
        "<h1>The page between the samples</h1>",
    )
    html = html.replace(
        "Version 2. Development clips only. The added checks are read from scores already saved. Not a conference submission.",
        "Version 3. The scene-cut-off result is unchanged. The same eighteen clips have been encoded again with x264's default scene-cut and keyframe interval. Not a held-out set, and not a viewer study.",
    )
    html = html.replace(
        "Nothing here is the held-out half, a viewer study, or a scene-cut-on encode. Choices among CRFs use only rungs the ladder already encoded.",
        "Nothing here is the held-out half or a viewer study. Section 6.5 is the scene-cut-on encode of these same clips. Choices among CRFs use only rungs that encode actually produced.",
    )
    old_second = (
        "The claim is this constructed page, libx264 at one CRF, scene-cut off, a GOP longer than the clip, and VMAF only."
    )
    new_second = (
        "The claim has two encoder settings. With scene-cut off and a GOP longer than the clip, the even-frame mean shortfall is "
        f"{off_mean:.2f}. With scene-cut left on, keyint 250 and scenecut 40, that mean is {on_mean:.2f}. "
        "The settled shortfall is zero on all twelve under the default encoder. "
        "One CRF still covers the whole file. The result is VMAF only."
    )
    if old_second not in html:
        raise SystemExit("abstract sentence not found")
    html = html.replace(old_second, new_second)
    old_limit = (
        "<p>Scene-cut detection was turned off, and the GOP is longer than the clip. "
        "Shorter keyframe intervals were not tried. An encoder left at its defaults may insert a keyframe on the cut and shrink the gap. "
        "That column has not been run on these eighteen files. Until it is, the result is the result for an encoder that was refused a reset at the cut, "
        "at one preset, with one CRF for the whole file.</p>"
    )
    new_limit = (
        "<p>Scene-cut detection was turned off in the first encode, and the GOP was longer than the clip. "
        "Section 6.5 runs the same clips again without those flags. The files use keyint 250, keyint_min 25, and scenecut 40, which is x264's own default string. "
        f"Ten of the twelve even-frame files have a keyframe on the cut into the page. "
        f"The mean falls from {off_mean:.2f} to {on_mean:.2f}. "
        f"It remains above zero on {still} clips, and the 9th-worst frame remains inside the page on all twelve. "
        "One preset and one rate-control mode were used. A different preset could move the keyframe or the score. "
        "The result is no longer only the result for an encoder that was refused a reset at the cut.</p>"
    )
    if old_limit not in html:
        raise SystemExit("limits paragraph not found")
    html = html.replace(old_limit, new_limit)
    old_end = (
        "It is a VMAF result. It is not yet a property of a held-out set, of scene-cut left on, of a shorter GOP, of another metric, or of a viewer."
    )
    new_end = (
        f"{close} "
        "It is a VMAF result. It is not yet a property of a held-out set, of another preset, of another metric, or of a viewer."
    )
    if old_end not in html:
        raise SystemExit("conclusion sentence not found")
    html = html.replace(old_end, new_end)
    marker = "  <h2>7. Discussion</h2>"
    if marker not in html:
        raise SystemExit("discussion heading not found")
    html = html.replace(marker, section + "\n" + marker)
    # The scene-cut-off bootstrap in version 2 was printed as 13.31. The resampling of these twelve values ends at off_hi.
    html = html.replace("7.83 to 13.31", f"{off_lo:.2f} to {off_hi:.2f}")
    html = html.replace(
        "  table {\n    width: 100%;",
        "  table.dense { font-size: 8pt; }\n"
        "  table.dense th, table.dense td { padding: 2px 3px; }\n"
        "  table {\n    width: 100%;",
    )
    old_encode = (
        "The decision encode is libx264, preset medium, yuv420p, scene-cut off, "
        "keyframe interval longer than the clip."
    )
    new_encode = (
        "The decision encode in sections 5 and 6.1 through 6.4 is libx264, preset medium, "
        "yuv420p, scene-cut off, keyframe interval longer than the clip. "
        "Section 6.5 repeats the same ladder with those restrictions omitted."
    )
    if old_encode not in html:
        raise SystemExit("method sentence not found")
    html = html.replace(old_encode, new_encode)
    old_tail = "Every 45th-worst score is still at least 90.1."
    if old_tail not in html:
        raise SystemExit("45th-worst sentence not found")
    html = html.replace(old_tail, "Every 45th-worst score is still above 90.")
    old_jump = (
        "At the CRF the even rule chose, the jump frame itself scores 0.0, 0.0, and 2.65. "
        "The frames after it score in the low 80s, like the rest of the page."
    )
    new_jump = (
        "At the CRF the even rule chose, the jump frame itself scores 0.0, 0.0, and 1.35. "
        "The next frame scores 81.4, 80.3, and 86.2."
    )
    if old_jump not in html:
        raise SystemExit("jump-frame sentence not found")
    html = html.replace(old_jump, new_jump)
    old_stress = "The study is a stress test for a check, built so the check can be wrong."
    new_stress = (
        "The study is a stress test for a check, built so the check can be wrong. "
        f"Section 6.5 leaves scene-cut on. The even-frame mean on these twelve clips falls from "
        f"{off_mean:.2f} to {on_mean:.2f}, the 9th-worst frame stays inside the page, "
        "and eleven of the twelve files still miss 90."
    )
    if old_stress not in html:
        raise SystemExit("discussion sentence not found")
    html = html.replace(old_stress, new_stress)
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT}")
    print(
        f"comparison off {off_mean:.2f} ({off_lo:.2f}-{off_hi:.2f}) "
        f"on {on_mean:.2f} ({on_lo:.2f}-{on_hi:.2f}) median {on_median:.2f} "
        f"shrink {sh_mean:.2f} still {still} settled_clear {settled_clear} "
        f"ninth_in {ninth_in} forty_out {forty_out} forty_min {forty_min:.2f}"
    )


if __name__ == "__main__":
    main()
