"""Write the analysis draft as HTML, then the caller prints it to PDF."""

from pathlib import Path

OUT = Path(__file__).resolve().parent / "the-page-between-the-samples.html"

INK = "#1c1c1c"
MUTED = "#444"
RULE = "#c8c8c8"
ACCENT = "#1f4b73"
BAR = "#8d3b3b"
OK = "#2c6b4a"
NEUTRAL = "#3e5166"


def esc(text):
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def grouped_bars(categories, series, y_max, y_label, suffix=""):
    width, height = 680, 250
    left, right, top, bottom = 46, 12, 16, 36
    inner_w = width - left - right
    inner_h = height - top - bottom
    n = len(categories)
    group = inner_w / n
    k = len(series)
    gap = 3
    bar_w = min(14, (group - 10) / k)

    parts = [
        f'<svg viewBox="0 0 {width} {height}" role="img">',
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="#fff"/>',
    ]
    for tick in range(5):
        value = y_max * tick / 4
        y = top + inner_h - (value / y_max) * inner_h
        parts.append(
            f'<line x1="{left}" y1="{y:.1f}" x2="{width - right}" y2="{y:.1f}" stroke="{RULE}" stroke-width="1"/>'
        )
        label = f"{value:.0f}{suffix}" if y_max >= 10 else f"{value:.1f}{suffix}"
        parts.append(
            f'<text x="{left - 6}" y="{y + 3:.1f}" text-anchor="end" font-size="10" fill="{MUTED}">{label}</text>'
        )
    parts.append(
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + inner_h}" stroke="{INK}" stroke-width="1"/>'
    )
    parts.append(
        f'<line x1="{left}" y1="{top + inner_h}" x2="{width - right}" y2="{top + inner_h}" stroke="{INK}" stroke-width="1"/>'
    )
    for i, cat in enumerate(categories):
        gx = left + i * group
        for s, (name, values, color) in enumerate(series):
            value = values[i]
            bh = 0 if y_max == 0 else (value / y_max) * inner_h
            x = gx + (group - (k * bar_w + (k - 1) * gap)) / 2 + s * (bar_w + gap)
            y = top + inner_h - bh
            parts.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bh:.1f}" fill="{color}"/>'
            )
        parts.append(
            f'<text x="{gx + group / 2:.1f}" y="{height - 14}" text-anchor="middle" font-size="10" fill="{MUTED}">{esc(cat)}</text>'
        )
    lx = left
    ly = 12
    # legend sits above the plot only if there is room; draw under the axis instead when one series
    legend = []
    for name, _values, color in series:
        legend.append(
            f'<rect x="{lx}" y="{height - 8}" width="8" height="8" fill="{color}"/>'
            f'<text x="{lx + 12}" y="{height - 1}" font-size="10" fill="{MUTED}">{esc(name)}</text>'
        )
        lx += 18 + len(name) * 5.4
    # move category labels up and legend to top-right of the chart title area: use a second row by shrinking
    parts = parts  # legend appended after we redo bottom; keep simple and put legend in a caption
    parts.append("</svg>")
    legend_html = " ".join(
        f'<span class="key"><i style="background:{color}"></i>{esc(name)}</span>'
        for name, _v, color in series
    )
    return "\n".join(parts) + f'<div class="legend">{legend_html}</div>'


def line_chart(xs, ys, y_min, y_max, href, hlabel):
    width, height = 680, 250
    left, right, top, bottom = 40, 12, 16, 32
    inner_w = width - left - right
    inner_h = height - top - bottom

    def px(i):
        return left + (i / (len(xs) - 1)) * inner_w

    def py(v):
        return top + (1 - (v - y_min) / (y_max - y_min)) * inner_h

    points = " ".join(f"{px(i):.1f},{py(v):.1f}" for i, v in enumerate(ys))
    hy = py(href)
    ticks = []
    for value in (75, 80, 85, 90, 95):
        y = py(value)
        ticks.append(
            f'<line x1="{left}" y1="{y:.1f}" x2="{width - right}" y2="{y:.1f}" stroke="{RULE}"/>'
            f'<text x="{left - 6}" y="{y + 3:.1f}" text-anchor="end" font-size="10" fill="{MUTED}">{value}</text>'
        )
    labels = []
    for frame in (530, 540, 550, 560):
        i = xs.index(frame)
        labels.append(
            f'<text x="{px(i):.1f}" y="{height - 12}" text-anchor="middle" font-size="10" fill="{MUTED}">{frame}</text>'
        )
    return f'''<svg viewBox="0 0 {width} {height}" role="img">
      <rect width="{width}" height="{height}" fill="#fff"/>
      {''.join(ticks)}
      <line x1="{left}" y1="{hy:.1f}" x2="{width - right}" y2="{hy:.1f}" stroke="{OK}" stroke-dasharray="4 3"/>
      <text x="{width - right - 2}" y="{hy - 4:.1f}" text-anchor="end" font-size="10" fill="{OK}">{hlabel}</text>
      <polyline fill="none" stroke="{BAR}" stroke-width="1.6" points="{points}"/>
      <line x1="{left}" y1="{top}" x2="{left}" y2="{top + inner_h}" stroke="{INK}"/>
      <line x1="{left}" y1="{top + inner_h}" x2="{width - right}" y2="{top + inner_h}" stroke="{INK}"/>
      {''.join(labels)}
    </svg>'''


def geometry():
    width = 680
    even = [56, 168, 281, 393, 506, 618, 731, 843]

    def x_of(frame, origin, span, left, inner):
        return left + ((frame - origin) / span) * inner

    marks = []
    for frame in even:
        x = x_of(frame, 0, 900, 36, 620)
        marks.append(f'<line x1="{x:.1f}" y1="28" x2="{x:.1f}" y2="52" stroke="{INK}" stroke-width="1.4"/>')
    page_x = x_of(538, 0, 900, 36, 620)
    page_w = x_of(558, 0, 900, 36, 620) - page_x
    zx = x_of(538, 480, 160, 36, 620)
    zw = x_of(558, 480, 160, 36, 620) - zx
    sx = x_of(546, 480, 160, 36, 620)
    sw = x_of(554, 480, 160, 36, 620) - sx
    return f'''<svg viewBox="0 0 {width} 150" role="img">
      <text x="36" y="14" font-size="11" fill="{MUTED}">Whole clip, 900 frames</text>
      <rect x="36" y="28" width="620" height="18" fill="#e6e6e6"/>
      <rect x="{page_x:.1f}" y="28" width="{max(page_w, 2):.1f}" height="18" fill="{ACCENT}"/>
      {''.join(marks)}
      <text x="36" y="62" font-size="10" fill="{MUTED}">0</text>
      <text x="640" y="62" font-size="10" fill="{MUTED}">899</text>
      <text x="36" y="86" font-size="11" fill="{MUTED}">Frames 480–640 of clip 01</text>
      <rect x="36" y="96" width="620" height="26" fill="#e6e6e6"/>
      <rect x="{zx:.1f}" y="96" width="{zw:.1f}" height="26" fill="{ACCENT}"/>
      <rect x="{sx:.1f}" y="122" width="{sw:.1f}" height="5" fill="{INK}"/>
      <text x="36" y="146" font-size="10" fill="{MUTED}">480</text>
      <text x="{zx:.1f}" y="146" font-size="10" fill="{INK}">page 538</text>
      <text x="630" y="146" font-size="10" fill="{MUTED}">640</text>
    </svg>'''


def table(headers, rows, aligns=None):
    aligns = aligns or ["left"] * len(headers)
    head = "".join(f"<th>{esc(h)}</th>" for h in headers)
    body = []
    for row in rows:
        cells = "".join(
            f'<td class="{aligns[i]}">{esc(cell)}</td>' for i, cell in enumerate(row)
        )
        body.append(f"<tr>{cells}</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"


shortfall = grouped_bars(
    ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"],
    [("Even frames", [8.11, 8.43, 20.42, 8.51, 7.23, 7.84, 8.26, 9.53, 20.69, 10.31, 3.72, 10.77], BAR)],
    24,
    "Points below VMAF 90. Settled is 0 on every clip.",
)
size = grouped_bars(
    ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"],
    [("Extra bytes", [38.5, 24.5, 46.9, 20.0, 19.1, 16.7, 30.7, 18.9, 41.2, 28.1, 15.0, 25.6], NEUTRAL)],
    50,
    "Percent more bytes than the even-frame file.",
    suffix="%",
)
miss = grouped_bars(
    ["8", "20", "40", "60", "90", "112", "150"],
    [("Starts that miss every even frame", [93.9, 84.6, 67.6, 48.4, 19.6, 0.4, 0], ACCENT)],
    100,
    "Hold length in frames. Percent of legal starts.",
    suffix="%",
)
boundary = grouped_bars(
    ["13", "14", "15", "16", "17", "18"],
    [("Even frames", [0.76, 1.30, 6.05, 7.62, 3.84, 4.87], BAR)],
    8,
    "Points below VMAF 90. Settled is 0. Not in the 10.32 mean.",
)
trace_x = list(range(528, 569))
trace_y = [
    92.28, 92.26, 92.25, 92.23, 92.22, 92.22, 92.22, 92.22, 92.22, 92.22,
    81.78, 81.82, 81.42, 81.78, 81.71, 81.80, 81.89, 81.92, 81.92, 81.91,
    81.89, 81.90, 81.91, 81.90, 81.90, 81.91, 81.91, 81.91, 81.90, 81.89,
    91.60, 91.60, 91.54, 91.64, 91.67, 91.65, 91.65, 91.67, 91.70, 91.70, 91.71,
]

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>The page between the samples</title>
<style>
  @page {{ size: letter; margin: 0.75in 0.8in 0.8in 0.8in; }}
  * {{ box-sizing: border-box; }}
  html, body {{ margin: 0; padding: 0; }}
  body {{
    font-family: "Palatino Linotype", Palatino, "Book Antiqua", Georgia, serif;
    color: {INK};
    font-size: 11.5pt;
    line-height: 1.45;
  }}
  h1 {{
    font-size: 18pt;
    font-weight: 600;
    line-height: 1.2;
    text-align: center;
    margin: 0 0 8px;
  }}
  .authors, .status {{
    text-align: center;
    margin: 0;
  }}
  .authors {{ font-size: 11.5pt; }}
  .status {{ color: {MUTED}; font-size: 10pt; font-style: italic; margin-top: 4px; }}
  h2 {{
    font-size: 13.5pt;
    font-weight: 600;
    margin: 1.15em 0 0.35em;
    page-break-after: avoid;
  }}
  h3 {{
    font-size: 12pt;
    font-weight: 600;
    margin: 0.9em 0 0.3em;
    page-break-after: avoid;
  }}
  p {{ margin: 0 0 0.7em; text-align: justify; hyphens: auto; }}
  .note {{
    border: 1px solid #b9a06a;
    padding: 8px 12px;
    margin: 14px 0 4px;
    font-size: 10.5pt;
    page-break-inside: avoid;
  }}
  figure {{
    margin: 0.8em 0 1em;
    page-break-inside: avoid;
  }}
  figcaption {{
    font-size: 9.5pt;
    color: {MUTED};
    margin-top: 4px;
    text-align: left;
  }}
  svg {{ width: 100%; height: auto; display: block; }}
  .legend {{ font-size: 9.5pt; color: {MUTED}; margin-top: 2px; }}
  .key {{ margin-right: 14px; }}
  .key i {{
    display: inline-block;
    width: 8px;
    height: 8px;
    margin-right: 4px;
    vertical-align: baseline;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 9pt;
    margin: 0.4em 0 0.2em;
    page-break-inside: avoid;
  }}
  th, td {{
    border-bottom: 1px solid {RULE};
    padding: 3px 5px;
    vertical-align: top;
  }}
  th {{
    text-align: left;
    font-weight: 600;
    border-bottom: 1px solid {INK};
  }}
  td.right, th.right {{ text-align: right; }}
  .refs p {{
    font-size: 10pt;
    text-align: left;
    margin: 0 0 0.45em;
    padding-left: 1.6em;
    text-indent: -1.6em;
  }}
  a {{ color: inherit; text-decoration: none; }}
</style>
</head>
<body>
  <h1>The page between the samples</h1>
  <p class="authors">Juan Miguel Miranda, Jean Khladyn Stefanie Abarquez, and Kimberly Klaire Gamboa</p>
  <p class="status">Draft for analysis. Development clips only. Not a conference submission.</p>

  <div class="note">The numbers below are the 12 comparison clips in clips/decisions.csv. Six medium pages are reported separately and are not in the mean. Nothing here is the held-out half, a viewer study, or a scene-cut-on encode.</div>

  <h2>Abstract</h2>
  <p>A thirty-second screen recording can be an easy picture except for a page of dense text that lasts twenty frames, about two-thirds of a second. Two ordinary checks can look at that file and agree that it is fine. Eight frames spread evenly through the nine hundred frames sit about a hundred and twelve frames apart, so the page fits in the gap. A fifth-percentile score of the same file is about the forty-fifth-worst frame, and twenty bad frames are not enough to move it. On the file those eight spread frames actually chose, the ninth-worst frame fell inside the page on all twelve comparison clips, and the forty-fifth-worst frame fell outside it on all twelve, still at or above VMAF 90.</p>
  <p>Taking the same budget of eight frames from the picture that has settled, eight frames after the cut, chooses a gentler x264 CRF. On these twelve clips that file misses 90 by nothing. The spread file misses 90 by 10.32 points on average. A 10,000-draw bootstrap of that paired gap, seed 20261010, has a 95% interval from 7.83 to 13.31. The settled file is larger: 27% more bytes on average, from 15% to 47% on a single clip, about 46 KB. The claim stops at scripted hard cuts between stills, libx264 at one CRF with scene-cut off and a GOP longer than the clip, VMAF only, and a page short enough to hide from both checks.</p>

  <h2>1. The agreement that is wrong</h2>
  <p>Lecture recordings and software tutorials are often signed off with a small sample and a single score for the file. The sample is there to stand in for the clip. The score is there to keep the worst moments from being averaged away. Both can be aimed at the easy picture while the only page a person has to read is already the damaged part.</p>
  <p>The geometry is simple. At 30 frames per second, 900 frames is 30 seconds. Eight centers of equal bins fall at frames 56, 168, 281, 393, 506, 618, 731, and 843. The gap between neighbors is a little over a hundred frames, more than three seconds. A page held for 20 frames does not have to be hidden on purpose. If its start is drawn uniformly from frame 180 through frame 700, the range used in this study, 84.6% of those starts miss every even center. A hold of about 112 frames, the gap itself, almost never misses. A hold of 150 frames never does.</p>
  <p>The score has the same hole. Sorted from worst to best, the 5th percentile of 900 frames is the 45th-worst. Twenty poor frames are fewer than forty-five, so that mark can sit on the easy picture. The 1st percentile is the 9th-worst. Twenty poor frames are enough to fill it. The two percentiles are not two views of one fact. One of them can see the page and the other cannot.</p>
  <figure>
    {geometry()}
    <figcaption>Figure 1. Clip 01, an agenda slide cut to a Wikipedia article at frame 538 and back at frame 558. The tall marks are the eight even frames. None of them lands on the page. The accent bar is the 20-frame page. The dark strip under the zoom is the settled sample, frames 546–553. Source: clips/log.csv and the even-frame list computed after the file existed.</figcaption>
  </figure>

  <h2>2. How often the spread misses</h2>
  <p>Figure 2 is calculated, not measured. For each hold length the start is every integer from 180 through 700 whose hold still ends by frame 899. A start is a hit if any of the eight even centers falls inside the hold. The curve is the reason for a 20-frame page. At that length the miss is the common case. The eighteen starts drawn from seed 20261010 all missed, which is what that curve predicts, and the draws were not moved afterward.</p>
  <figure>
    {miss}
    <figcaption>Figure 2. Calculated miss rate of eight even centers. The study’s page is the bar at 20 frames: 84.6% of legal starts miss every even frame.</figcaption>
  </figure>

  <h2>3. What this is, and what it is next to</h2>
  <p>Shot cuts have been found from pixel differences for a long time. A hard cut is the easy case: the brightness of the frame jumps, and a small threshold separates it from a still [6]. This paper uses that comparison as a clock, not as a new detector. The mean absolute difference of the luma plane, above 2 on 8-bit levels, marks the cut. The sample waits eight frames, about a quarter of a second, and then takes the next eight frames of the same picture, stopping if the picture changes again. The wait is there because the jump frame itself is a poor thing to score.</p>
  <p>VMAF scores frames one by one and already warns that a mean hides the tail [1]. Its own pooling can take a percentile [2]. On a clip this long the 5th percentile is still coarser than a 20-frame hole. The file score used here is the 9th-worst of the 900 frame scores from one full pass, which is the 1st percentile of a clip of this length. The 45th-worst is reported so the coarser mark can be seen. It does not choose the CRF.</p>
  <p>The encoder is x264 at one constant rate factor for the whole file [3]. A higher CRF is a smaller, rougher file. Scene-cut detection is off and the group of pictures is longer than the clip, so the cut is not handed a fresh keyframe. That is a choice of the experiment. It is also the setting a reviewer can most fairly call artificial, and it is named as such in the limits. No other codec, preset, or rate-control mode was compared, and the page was not given its own CRF. Subjective methods exist for the question a viewer would actually be asked [4], [5]. No viewer was shown these files. MS-SSIM and PSNR were not run [7]. VMAF 90 is the score that was used. It is not a reading score.</p>

  <h2>4. The clips and the choice</h2>
  <p>Each clip is 1920×1080, 30 frames per second, exactly 900 frames. It holds one easy screen picture, cuts to one dense page for exactly 20 frames, and cuts back. There is no fade. The easy pictures in the comparison set are flat screen graphics with large type and open space: an agenda slide, an empty dashboard, an empty editor, a section divider, a geometric desktop, and a one-line editor on a geometric wallpaper. Each is used twice. The dense pages are a Wikipedia article, a page of C, a protocol article, language documentation, a population table, and a terminal listing. Six further clips replace the easy picture with a busier but still readable screen: a status page, a word processor, a kanban board, a sound panel, a file manager, and an appearance panel. Those six are the boundary. They stay out of the mean.</p>
  <p>The reference is a lossless long-GOP encode, so repeated frames stay small and the pixels match the stills. The decision encode is libx264, preset medium, yuv420p, scene-cut off, keyframe interval longer than the clip. The ladder starts at CRF 28, 32, 36, 40, and 44, then steps by 2 until a rule’s own vote crosses 90. A rule may keep a CRF only while the worst of its eight VMAF scores is still at least 90. It keeps the highest such CRF. If no rung qualifies, that rule has no file. The step is 2, so an integer between rungs was not encoded. On several clips the even-frame vote is not perfectly monotone as CRF rises, so that search can miss a legal rung. Votes are indexes into one saved list of 900 scores. They are not a second video. Both sides of VMAF are converted to yuv420p. A 4:4:4 encode was not compared, so chroma subsampling is not separated from the CRF.</p>
  <p>Five ways of spending the eight frames are scored from that list. Even frames, ignoring the picture. Eight frames starting eight after the cut. Eight frames starting on the cut. Eight random frames from one draw, seed 20261010, written down before scoring: 196, 353, 297, 306, 110, 775, 94, and 695. And the eight frames of highest luma variance on the uncompressed picture. On a still hold, that last rule lands on whichever of the two pictures is more detailed, and then takes eight identical frames of it.</p>
  <p>The cut finder was run as ordinary C, as the same C with the compiler free to vectorize, and as AVX2. The three cut lists matched on every clip. That check is the course work. It is not the result of this paper. The paper does not claim that choosing the frames is fast. The three kernels and one VMAF pass were timed. The rest of the path, from decode through the CRF search, was not. One VMAF pass on this machine took about 21 seconds, and the brightness sum took well under a second. Those two numbers are not a pipeline benchmark.</p>

  <h2>5. What the spread file looks like</h2>
  <p>Figure 3 is clip 01 at the CRF the even frames chose, CRF 36. Through the easy slide the score sits near 92. At frame 538, the cut onto the article, it drops to about 82 and stays there for the twenty frames of text. At frame 558 it returns to about 91. The settled sample, frames 546–553, sits in the dip. The nearest even frames are 506 and 618, both on the slide. The 9th-worst frame of this file is frame 548, inside the page, at 81.9. The 45th-worst is frame 687, on the slide, at 91.7.</p>
  <figure>
    {line_chart(trace_x, trace_y, 75, 96, 90, "90")}
    <figcaption>Figure 3. Frame-by-frame VMAF, clip 01, CRF 36, frames 528–568. The page is frames 538–557. Source: clips/work/01/scores/crf36.json.</figcaption>
  </figure>
  <p>That pattern is the whole comparison set, not one lucky clip. On the spread-chosen file of each of the twelve, the 9th-worst frame is inside the twenty-frame page, and the 45th-worst frame is outside it. Every 45th-worst score is still at least 90.1. A reader who published the 5th percentile would report a pass. A reader who opened the page would not.</p>

  <h2>6. Results</h2>
  <h3>6.1 Even frames against settled frames</h3>
  <p>The settled rule clears 90 on every comparison clip. The even rule does not clear it on any of them. The mean of the twelve shortfalls is 10.32. Two clips, an empty editor against a protocol page and the same editor against language documentation, miss by about 20 points, with a 9th-worst score near 69. The smallest miss is 3.72, a geometric desktop against a terminal listing. The bootstrap interval above is the uncertainty of this mean under resampling of these twelve clips. It is not a confidence interval for a larger population, and it is not the held-out test.</p>
  <figure>
    {shortfall}
    <figcaption>Figure 4. Shortfall of the even-frame file below VMAF 90. Settled shortfall is 0 on every comparison clip. Source: clips/decisions.csv.</figcaption>
  </figure>
  {table(
    ["Clip", "Pages", "Even CRF", "Settled CRF", "Even 9th", "Settled 9th", "Gap", "Size"],
    [
      ["01", "Agenda / article", "36", "31", "81.9", "90.3", "8.11", "+38%"],
      ["02", "Dashboard / source", "37", "32", "81.6", "90.6", "8.43", "+25%"],
      ["03", "Editor / protocol", "40", "31", "69.6", "90.5", "20.42", "+47%"],
      ["04", "Section / docs", "36", "31", "81.5", "91.4", "8.51", "+20%"],
      ["05", "Grid / table", "35", "30", "82.8", "90.8", "7.23", "+19%"],
      ["06", "Editor desktop / terminal", "37", "32", "82.2", "90.5", "7.84", "+17%"],
      ["07", "Agenda / source", "37", "32", "81.7", "90.2", "8.26", "+31%"],
      ["08", "Dashboard / protocol", "36", "31", "80.5", "90.0", "9.53", "+19%"],
      ["09", "Editor / docs", "40", "31", "69.3", "91.3", "20.69", "+41%"],
      ["10", "Section / table", "36", "30", "79.7", "91.2", "10.31", "+28%"],
      ["11", "Grid / terminal", "35", "32", "86.3", "90.5", "3.72", "+15%"],
      ["12", "Editor desktop / article", "37", "31", "79.2", "90.2", "10.77", "+26%"],
    ],
    ["left", "left", "right", "right", "right", "right", "right", "right"],
  )}
  <p class="status" style="text-align:left;margin-top:2px">Table 1. Comparison set. Gap is the even-frame shortfall. Size is the settled file against the even-frame file.</p>
  <p>The settled CRF is 5.7 steps lower on average. The file grows by 45,927 bytes on average. Target 80, scored the same way and not used to choose, still fails on four of the twelve spread files, clips 03, 09, 10, and 12. Their mean shortfall at 80, taken over all twelve, is 1.85. The settled files are at or above 80 on every clip.</p>
  <figure>
    {size}
    <figcaption>Figure 5. File-size cost of the settled choice on the comparison set.</figcaption>
  </figure>

  <h3>6.2 The other ways to spend eight frames</h3>
  <p>Random frames behave like even frames unless a drawn frame happens to land in the page. Two of the eight shared random frames do. Frame 230 falls in clip 03’s page, and the random rule there stops at CRF 36 instead of the even rule’s CRF 40. Frame 353 falls in clip 11’s page, and the random file then matches the settled file, shortfall zero. Across the twelve, the random mean shortfall is 9.00. One shared draw is not a second method. It is the even method with a chance of a hit.</p>
  <p>Frames that start on the cut match the settled file on the nine clips where a CRF still clears 90. On clips 04, 08, and 11 no rung does. At the CRF the even rule chose, the jump frame itself scores 0.0, 0.0, and 2.65. The frames after it score in the low 80s, like the rest of the page. The minimum of a sample that includes the jump is the jump. That is why the method waits.</p>
  <p>Highest luma variance is not a substitute for finding the cut. On clips 01 and 02 the text page is the more detailed picture, and the rule matches settled. On eight clips the easy picture is more detailed, the eight frames are the first eight frames of the clip, and the shortfall is as large as the even rule’s or larger. On clips 08 and 11 the detailed frames begin on the cut, and the rule has no file, for the same reason the on-cut rule has none. Mean shortfall of the ten files it did choose is 10.13.</p>
  {table(
    ["Rule", "Files chosen", "Mean shortfall", "Where the eight frames landed"],
    [
      ["Even frames", "12 of 12", "10.32", "All on the easy picture. The 9th-worst frame of the file is inside the page."],
      ["Settled, cut + 8", "12 of 12", "0.00", "Inside the page on every clip."],
      ["On the cut", "9 of 12", "0.00", "Matches settled where it chooses. No file on 04, 08, and 11."],
      ["One random draw", "12 of 12", "9.00", "Hits the page on clips 03 and 11 only."],
      ["Highest variance", "10 of 12", "10.13", "Matches settled on 01 and 02. Samples the easy picture on eight clips."],
    ],
  )}
  <p class="status" style="text-align:left;margin-top:2px">Table 2. Comparison set only. The on-cut and variance means are over the files those rules were allowed to choose, not over the clips they skipped.</p>

  <h3>6.3 Medium pages, kept out of the mean</h3>
  <p>The six boundary clips use a screen that already has labels, cards, or toolbars, cut to the same kind of dense page for twenty frames. The direction does not reverse. Settled shortfall is zero on all six. Even-frame shortfall averages 4.07, from 0.76 on the status page to 7.62 on the sound panel. The gaps are smaller because the easy picture is no longer nearly free to compress, so the even rule cannot go as harsh. Clip 13 is the useful exception on size: settled CRF 31 produced a slightly smaller file than even CRF 32, 307,381 bytes against 310,307. x264’s size is not a smooth function of CRF. A gentler setting is usually larger here. It is not larger by a law.</p>
  <figure>
    {boundary}
    <figcaption>Figure 6. Boundary clips. Same shortfall as Figure 4, not included in the 10.32 mean. Source: clips/decisions.csv.</figcaption>
  </figure>

  <h2>7. Discussion</h2>
  <p>The result is a disagreement between the vote and the file. The even vote looks only at the easy picture, so it accepts a CRF whose damaged frames are exactly the page. The settled vote looks only at the page, so it refuses that CRF. Judged afterward by a mark tight enough to fall inside twenty frames, the second file is the one that holds 90. Judged by the 5th percentile, the first file would have been reported as holding it too.</p>
  <p>The cost is real and should be printed beside the score. Protecting two-thirds of a second costs, on this set, a little over a quarter more bytes and about six CRF steps. That is the trade on these stills. It is not a small constant, and it is not a doubling. Clips 03 and 09, where the even file falls to about 69, pay the most in both score and bytes.</p>
  <p>The other eight-frame rules do not rescue the even sample. A random draw misses unless it is lucky. Detail misses whenever the easy picture is the busier of the two, which is common once the easy picture is a colored desktop rather than a blank slide. The cut frame itself is the wrong place to read: VMAF can score the jump at zero while the settled page a few frames later is a coherent, merely soft, picture. The study waits eight frames. On these clips a wait of one, two, four, twelve, or sixteen frames, still off the jump, also holds the file. Eight is the rule that was locked. It is not a tuned optimum.</p>
  <p>None of this says that a short text page is typical of screen video. The page is short on purpose. If it stayed up for several seconds, the even frames would hit it and there would be little to measure. Figure 2 is that admission in advance. The study is a stress test for a check, built so the check can be wrong.</p>

  <h2>8. Limits</h2>
  <p>These twelve clips are a development set. The same pictures repeat. The starts were drawn before the files existed, and they were not moved to dodge the even frames, but a second set, scored only after the pipeline was frozen, is what a confirmation would be. The bootstrap resamples this set. It does not stand in for that second set.</p>
  <p>The pictures are stills joined by a hard cut. They are not a camera, not a scrolling page, and not a person moving a window. On every comparison clip, 99.8% of easy-frame pairs sit at or below the cut threshold of 2, and the planted cuts sit well above it. The threshold was not swept. A nearby value would still have found these cuts. That is not a test on flicker, fades, or motion. A recording that flickers, fades, or cuts every few seconds is a different question. The first settled picture would then not automatically be the page that matters.</p>
  <p>Scene-cut detection was turned off, and the GOP is longer than the clip. Shorter keyframe intervals were not tried. An encoder left at its defaults may insert a keyframe on the cut and shrink the gap. That column has not been run on these eighteen files. Until it is, the result is the result for an encoder that was refused a reset at the cut, at one preset, with one CRF for the whole file.</p>
  <p>One CRF covers the whole file. Giving the page its own strength, or switching codec, preset, or rate control, would be a different experiment and a different claim. VMAF is not a reading test, and no text-reading check was run. A soft page can score in the low 80s and still be the wrong thing to ship, or, on some type, still be readable. No one was asked. MS-SSIM and PSNR were not run, so the result is a VMAF result. Target 80 does not reverse the comparison on this set, but four spread files miss 80 as well as 90, so the story is not an artifact of the number 90 alone.</p>
  <p>Photographic pictures were not used. An earlier check on fur, gravel, and leaves, at a smaller frame size, had both rules pick the same gentle CRF. Those rows are not in this table. They are why this set stays on flat screen graphics and readable text.</p>

  <h2>9. Conclusion</h2>
  <p>Eight even frames and a 5th-percentile score can agree, and both can be looking at the easy picture. On twelve scripted screen clips, the file those eight frames chose has its 9th-worst frame inside a twenty-frame page every time, 10.32 points below VMAF 90 on average, while the 45th-worst frame stays outside the page and above 90. Eight frames taken a quarter of a second after the cut hold 90 on every one of those clips. The file is about 27% larger. The result is a property of a short page in a long easy stretch, with one libx264 CRF for the file, scene-cut off, and a GOP longer than the clip. It is a VMAF result. It is not yet a property of a held-out set, of scene-cut left on, of a shorter GOP, of another metric, or of a viewer.</p>

  <h2>References</h2>
  <div class="refs">
    <p>[1] Z. Li, A. Aaron, I. Katsavounidis, A. Moorthy, and M. Manohara, “Toward a practical perceptual video quality metric,” Netflix Technology Blog, 2016.</p>
    <p>[2] Netflix, libvmaf, percentile pooling of the per-frame score. https://github.com/Netflix/vmaf</p>
    <p>[3] VideoLAN, x264. Constant rate factor and scene-cut detection as exposed by FFmpeg. https://trac.ffmpeg.org/wiki/Encode/H.264</p>
    <p>[4] ITU-T Recommendation P.910, Subjective video quality assessment methods for multimedia applications.</p>
    <p>[5] ITU-R Recommendation BT.500, Methodologies for the subjective assessment of the quality of television images.</p>
    <p>[6] A. Hanjalic, “Shot-boundary detection: Unraveled and resolved?” IEEE Transactions on Circuits and Systems for Video Technology, vol. 12, no. 2, pp. 90–105, 2002.</p>
    <p>[7] Z. Wang, A. C. Bovik, H. R. Sheikh, and E. P. Simoncelli, “Image quality assessment: From error visibility to structural similarity,” IEEE Transactions on Image Processing, vol. 13, no. 4, pp. 600–612, 2004.</p>
  </div>
</body>
</html>
'''

OUT.write_text(html, encoding="utf-8")
print(OUT)
