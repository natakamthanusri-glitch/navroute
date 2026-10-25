import streamlit as st
import heapq
import plotly.graph_objects as go

st.set_page_config(
    page_title="SmartRoute",
    page_icon="🗺️",
    layout="wide"
)

graph = {
    "LIBRARY": {"U-BLOCK": 1},
    "U-BLOCK": {
        "LIBRARY": 1, "A-BLOCK": 1, "H-BLOCK": 1
    },
    "A-BLOCK": {"U-BLOCK": 1, "CANTEEN": 1},
    "H-BLOCK": {"U-BLOCK": 1, "LABS": 1},
    "CANTEEN": {"A-BLOCK": 1, "MAIN GATE": 1},
    "LABS": {"H-BLOCK": 1, "MAIN GATE": 1},
    "MAIN GATE": {"CANTEEN": 1, "LABS": 1}
}

coordinates = {
    "LIBRARY": (0, 4),
    "U-BLOCK": (0, 3),
    "A-BLOCK": (-1, 2),
    "H-BLOCK": (1, 2),
    "CANTEEN": (-1, 1),
    "LABS": (1, 1),
    "MAIN GATE": (0, 0)
}

def a_star(start, goal, blocked=None):
    blocked = blocked or set()
    queue = [(0, 0, start, [start])]
    best = {start: 0}
    explored = set()

    while queue:
        _, cost, node, path = heapq.heappop(queue)

        if cost != best.get(node):
            continue
        if node in explored:
            continue

        explored.add(node)

        if node == goal:
            return path, cost, len(explored)

        for nxt, distance in graph[node].items():
            if frozenset((node, nxt)) in blocked:
                continue

            new_cost = cost + distance

            if new_cost < best.get(nxt, float("inf")):
                best[nxt] = new_cost
                heapq.heappush(
                    queue,
                    (new_cost, new_cost, nxt, path + [nxt])
                )

    return None, None, len(explored)

def draw_map(path=None, blocked=None):
    path = path or []
    blocked = blocked or set()
    fig = go.Figure()
    drawn = set()

    for node, neighbors in graph.items():
        for nxt in neighbors:
            road = frozenset((node, nxt))
            if road in drawn:
                continue
            drawn.add(road)

            x1, y1 = coordinates[node]
            x2, y2 = coordinates[nxt]

            color = (
                "red" if road in blocked
                else "#16a34a" if any(
                    frozenset((path[i], path[i + 1])) == road
                    for i in range(len(path) - 1)
                )
                else "#aab7c4"
            )

            fig.add_trace(go.Scatter(
                x=[x1, x2], y=[y1, y2],
                mode="lines",
                line=dict(color=color, width=5),
                hoverinfo="text",
                text=f"{node} ↔ {nxt}",
                showlegend=False
            ))

    for node, (x, y) in coordinates.items():
        color = (
            "#16a34a" if path and node == path[0]
            else "#2563eb" if path and node == path[-1]
            else "#163b72"
        )
        fig.add_trace(go.Scatter(
            x=[x], y=[y],
            mode="markers+text",
            text=[node],
            textposition="top center",
            marker=dict(size=18, color=color),
            showlegend=False
        ))

    fig.update_layout(
        height=480,
        paper_bgcolor="white",
        plot_bgcolor="white",
        xaxis=dict(visible=False, range=[-2, 2]),
        yaxis=dict(visible=False, range=[-0.5, 4.7]),
        margin=dict(l=10, r=10, t=20, b=10)
    )
    return fig

st.title("🗺️ SmartRoute")
st.caption("Smart Campus Route Planner using A* Search")

locations = list(graph.keys())

with st.sidebar:
    st.header("Plan Your Journey")
    start = st.selectbox("Starting Location", locations, index=0)
    goal = st.selectbox(
        "Destination", locations, index=len(locations) - 1
    )

    road_options = []
    for node in graph:
        for nxt in graph[node]:
            if locations.index(node) < locations.index(nxt):
                road_options.append(f"{node} ↔ {nxt}")

    selected = st.multiselect("🚧 Blocked Roads", road_options)

blocked = {
    frozenset(label.split(" ↔ ")) for label in selected
}

if start == goal:
    st.success(f"You are already at {start}.")
    path, cost, explored = [start], 0, 1
else:
    path, cost, explored = a_star(start, goal, blocked)

if path:
    c1, c2, c3 = st.columns(3)
    c1.metric("Route Cost", cost)
    c2.metric("Stops", len(path) - 1)
    c3.metric("Locations Explored", explored)

    st.subheader("Campus Map")
    st.plotly_chart(
        draw_map(path, blocked),
        use_container_width=True
    )

    st.subheader("Shortest Route")
    st.success(" → ".join(path))

    st.subheader("Step-by-Step Directions")
    for i, place in enumerate(path):
        if i == 0:
            st.write(f"🟢 Step {i + 1}: Start at {place}")
        elif i == len(path) - 1:
            st.write(f"🏁 Step {i + 1}: Arrive at {place}")
        else:
            st.write(f"🚶 Step {i + 1}: Walk to {place}")

    alternatives = []
    for i in range(len(path) - 1):
        road = frozenset((path[i], path[i + 1]))
        alt, alt_cost, _ = a_star(
            start, goal, blocked | {road}
        )
        if alt and alt != path:
            alternatives.append((alt_cost, alt))

    st.subheader("Alternative Route")
    if alternatives:
        alt_cost, alt_path = min(alternatives)
        st.info(" → ".join(alt_path))
        st.write(f"Alternative route cost: {alt_cost}")
    elif start != goal:
        st.warning("No alternative route is available.")
else:
    st.error("No route available. Please unblock a road.")
