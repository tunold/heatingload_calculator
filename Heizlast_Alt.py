import math
import streamlit as st


def calculate_heating_demand(volume_m3: float, heat_loss_factor_W_per_m3K: float, delta_t_K: float) -> float:
    """
    Einfache Überschlagsrechnung:
        Q = V * H * ΔT

    Returns:
        Heizlast in kW
    """
    return volume_m3 * heat_loss_factor_W_per_m3K * delta_t_K / 1000.0


def _geometry(length_a_m: float,
              length_b_m: float,
              room_height_m: float,
              floors: int,
              roof_pitch_deg: float,
              ridge_axis: str,
              window_area_m2: float) -> dict:
    """
    Geometrie für rechteckigen Grundriss mit Satteldach.
    """
    floor_area_single = length_a_m * length_b_m
    gross_floor_area = floor_area_single * floors
    volume = floor_area_single * room_height_m * floors

    # vereinfachte Dachfläche (wie im Original): geneigte Fläche als Projektion / cos(pitch)
    pitch_rad = math.radians(roof_pitch_deg)
    cos_pitch = max(math.cos(pitch_rad), 1e-6)
    if ridge_axis == "A":
        roof_area = (length_b_m / cos_pitch) * length_a_m
    else:
        roof_area = (length_a_m / cos_pitch) * length_b_m

    wall_area_gross = (length_a_m + length_b_m) * room_height_m * floors
    wall_area_net = max(wall_area_gross - window_area_m2, 0.0)

    return {
        "floor_area_single": floor_area_single,
        "gross_floor_area": gross_floor_area,
        "volume": volume,
        "roof_area": roof_area,
        "wall_area_gross": wall_area_gross,
        "wall_area_net": wall_area_net,
        "window_area": window_area_m2,
    }


def calculate_heating_demand_detailed(length_a_m: float,
                                     length_b_m: float,
                                     room_height_m: float,
                                     floors: int,
                                     roof_pitch_deg: float,
                                     ridge_axis: str,
                                     u_wall_W_m2K: float,
                                     u_roof_W_m2K: float,
                                     u_floor_W_m2K: float,
                                     infiltration_W_m3K: float,
                                     delta_t_K: float,
                                     u_window_W_m2K: float,
                                     window_area_m2: float):
    """
    Detaillierte Heizlast:
      - Transmission über Wand/Dach/Boden/Fenster (U*A*ΔT)
      - Infiltration als volumetrischer Faktor (H_v * V * ΔT)

    Returns:
      total_kW, infiltration_kW, hull_kW, parts_kW_dict, geom_dict
    """
    geom = _geometry(length_a_m, length_b_m, room_height_m, floors, roof_pitch_deg, ridge_axis, window_area_m2)

    q_wall_kW = u_wall_W_m2K * geom["wall_area_net"] * delta_t_K / 1000.0
    q_roof_kW = u_roof_W_m2K * geom["roof_area"] * delta_t_K / 1000.0

    # Bodenplatte typischerweise nur EG-Grundfläche (nicht *floors)
    q_floor_kW = u_floor_W_m2K * geom["floor_area_single"] * delta_t_K / 1000.0

    q_window_kW = u_window_W_m2K * geom["window_area"] * delta_t_K / 1000.0

    q_hull_kW = q_wall_kW + q_roof_kW + q_floor_kW + q_window_kW
    q_infil_kW = infiltration_W_m3K * geom["volume"] * delta_t_K / 1000.0

    parts = {
        "Wand": q_wall_kW,
        "Dach": q_roof_kW,
        "Boden": q_floor_kW,
        "Fenster": q_window_kW,
        "Infiltration": q_infil_kW,
    }

    return q_hull_kW + q_infil_kW, q_infil_kW, q_hull_kW, parts, geom


def _preset_defaults(preset: str) -> dict:
    """
    Sehr grobe Default-Werte (als Startpunkt) – Nutzer kann immer nachjustieren.
    """
    presets = {
        "Altbau": dict(u_wall=1.6, u_roof=1.2, u_floor=1.0, u_window=4.8, infil=0.20),
        "Teilsaniert": dict(u_wall=0.8, u_roof=0.6, u_floor=0.5, u_window=1.6, infil=0.08),
        "Neubau": dict(u_wall=0.25, u_roof=0.20, u_floor=0.25, u_window=1.0, infil=0.04),
        "Passivhaus": dict(u_wall=0.12, u_roof=0.10, u_floor=0.12, u_window=0.75, infil=0.02),
    }
    return presets.get(preset, presets["Teilsaniert"])


def main():
    st.set_page_config(page_title="Heizlastberechnung", page_icon="🔥", layout="wide")
    st.title("🔥 Heizlastberechnung")

    tab1, tab2 = st.tabs(["Detaillierte Berechnung", "Einfache Überschlagung (Volumen)"])

    # -----------------------------
    # TAB 1: Detailliert
    # -----------------------------
    with tab1:
        st.subheader("Detaillierte Heizlastberechnung (U·A·ΔT + Infiltration)")

        # Sidebar-ähnliche Eingabe links, Ergebnis rechts
        left, right = st.columns([1.05, 1.4], gap="large")

        with left:
            st.markdown("### Eingaben")

            preset = st.selectbox("Gebäudestandard (Startwerte)", ["Altbau", "Teilsaniert", "Neubau", "Passivhaus"], index=1)
            p = _preset_defaults(preset)

            with st.expander("Geometrie", expanded=True):
                length_a = st.number_input("Länge A [m]", min_value=1.0, value=10.0, step=0.5)
                length_b = st.number_input("Länge B [m]", min_value=1.0, value=5.0, step=0.5)
                room_height = st.number_input("Raumhöhe [m]", min_value=2.0, value=3.0, step=0.1)
                floors = st.number_input("Stockwerke", min_value=1, value=1, step=1)
                window_area = st.number_input("Fensterfläche [m²]", min_value=0.0, value=25.0, step=1.0)
                roof_pitch = st.slider("Dachneigung [°]", 0.0, 75.0, 30.0)
                ridge_axis = st.selectbox("Firstachse", ["A", "B"], index=0)

            with st.expander("Bauteile (U-Werte)", expanded=True):
                u_wall = st.number_input("U Wand [W/(m²K)]", min_value=0.05, max_value=5.0, value=float(p["u_wall"]), step=0.05,
                                         help="Typisch: Altbau ~1–2, Teilsaniert ~0.5–1, Neubau ~0.2–0.3")
                u_window = st.number_input("U Fenster [W/(m²K)]", min_value=0.30, max_value=7.0, value=float(p["u_window"]), step=0.05,
                                           help="Einfachverglasung ~5–6, 2-fach ~1.1–1.6, 3-fach ~0.7–1.0")
                u_roof = st.number_input("U Dach [W/(m²K)]", min_value=0.05, max_value=5.0, value=float(p["u_roof"]), step=0.05)
                u_floor = st.number_input("U Boden [W/(m²K)]", min_value=0.05, max_value=5.0, value=float(p["u_floor"]), step=0.05)

            with st.expander("Randbedingungen", expanded=True):
                delta_t = st.slider("Temperaturdifferenz ΔT [K]", 5.0, 35.0, 20.0,
                                    help="ΔT = T_innen − T_außen. (Numerisch gleich zu °C-Differenz.)")
                infiltration = st.number_input("Infiltration Hᵥ [W/(m³K)]", min_value=0.0, max_value=0.30, value=float(p["infil"]), step=0.01,
                                               help="Sehr grobes Modell für Lüftungs-/Undichtigkeitsverluste; multipliziert mit Gebäudevolumen.")

        # Berechnung + Plausibilitätschecks
        total_kW, q_infil_kW, q_hull_kW, parts, geom = calculate_heating_demand_detailed(
            length_a, length_b, room_height, int(floors),
            roof_pitch, ridge_axis,
            u_wall, u_roof, u_floor,
            infiltration, delta_t,
            u_window, window_area
        )

        with right:
            st.markdown("### Ergebnisse")

            # Plausibilität
            if window_area > geom["wall_area_gross"]:
                st.error("Fensterfläche ist größer als die gesamte Wandfläche. Bitte Eingaben prüfen.")
                st.stop()

            # KPI-Kacheln
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Gesamtheizlast", f"{total_kW:.2f} kW")
            c2.metric("Hülle", f"{q_hull_kW:.2f} kW")
            c3.metric("Infiltration", f"{q_infil_kW:.2f} kW")

            spec_W_m2 = (total_kW * 1000.0) / max(geom["floor_area_single"], 1e-6)
            c4.metric("Spezifisch", f"{spec_W_m2:.0f} W/m²")

            st.divider()

            st.markdown("#### Aufschlüsselung")
            # Bar chart ohne Infiltration doppelt in "Hülle"
            chart_data = {k: v for k, v in parts.items()}
            st.bar_chart(chart_data)

            st.divider()

            # Details kompakt
            with st.expander("Geometrie-Details"):
                st.write({
                    "Grundfläche (1 Geschoss) [m²]": round(geom["floor_area_single"], 2),
                    "Brutto-Geschossfläche [m²]": round(geom["gross_floor_area"], 2),
                    "Volumen [m³]": round(geom["volume"], 2),
                    "Wandfläche brutto [m²]": round(geom["wall_area_gross"], 2),
                    "Wandfläche netto [m²]": round(geom["wall_area_net"], 2),
                    "Dachfläche [m²]": round(geom["roof_area"], 2),
                })

            with st.expander("Hinweise"):
                if infiltration >= 0.15:
                    st.warning("Infiltration ist relativ hoch – das kann bei Altbau/Undichtigkeiten realistisch sein, "
                               "führt aber zu stark steigender Heizlast. Prüfe Annahmen (Lüftung, Dichtigkeit, Volumen).")
                if u_wall > 1.5 or u_window > 3.0:
                    st.info("Hohe U-Werte: oft große Hebel bei Sanierung (Fassade/Fenster).")

            # Download: Ergebnis JSON
            result_payload = {
                "inputs": {
                    "length_a_m": length_a,
                    "length_b_m": length_b,
                    "room_height_m": room_height,
                    "floors": int(floors),
                    "roof_pitch_deg": roof_pitch,
                    "ridge_axis": ridge_axis,
                    "window_area_m2": window_area,
                    "u_wall_W_m2K": u_wall,
                    "u_window_W_m2K": u_window,
                    "u_roof_W_m2K": u_roof,
                    "u_floor_W_m2K": u_floor,
                    "delta_t_K": delta_t,
                    "infiltration_W_m3K": infiltration,
                },
                "geometry": geom,
                "results_kW": {
                    "total": total_kW,
                    "hull": q_hull_kW,
                    "infiltration": q_infil_kW,
                    "parts": parts,
                }
            }
            st.download_button(
                "Ergebnis als JSON herunterladen",
                data=str(result_payload),
                file_name="heizlast_ergebnis.json",
                mime="application/json"
            )

    # -----------------------------
    # TAB 2: Einfacher Überschlag
    # -----------------------------
    with tab2:
        st.subheader("Einfache Überschlagung über Volumen")

        left, right = st.columns([1.05, 1.4], gap="large")

        with left:
            st.markdown("### Eingaben")
            with st.expander("Geometrie", expanded=True):
                floor_area = st.number_input("Grundfläche [m²]", min_value=10.0, max_value=1000.0, value=100.0, step=5.0)
                room_height_simple = st.number_input("Raumhöhe [m]", min_value=2.0, max_value=10.0, value=3.0, step=0.1)
                floors_simple = st.number_input("Stockwerke", min_value=1, max_value=20, value=1, step=1)
                volume_simple = floor_area * room_height_simple * int(floors_simple)

            with st.expander("Wärmeverlustfaktor", expanded=True):
                heat_loss_factor = st.slider(
                    "Wärmeverlustfaktor H [W/(m³K)]",
                    min_value=0.05, max_value=2.0, value=1.0, step=0.05,
                    help="Grobe Erfahrungswerte: Altbau ~1.0–1.5; modern ~0.3–0.8; Passivhaus ~0.15–0.25"
                )

            delta_t_simple = st.slider("Temperaturdifferenz ΔT [K]", 5.0, 35.0, 15.0)

        with right:
            st.markdown("### Ergebnis")
            q_simple_kW = calculate_heating_demand(volume_simple, heat_loss_factor, delta_t_simple)

            c1, c2, c3 = st.columns(3)
            c1.metric("Volumen", f"{volume_simple:.0f} m³")
            c2.metric("Heizlast", f"{q_simple_kW:.2f} kW")
            spec_W_m2_simple = (q_simple_kW * 1000.0) / max(floor_area, 1e-6)
            c3.metric("Spezifisch", f"{spec_W_m2_simple:.0f} W/m²")

            st.divider()

            st.write(
                f"Mit H = {heat_loss_factor:.2f} W/(m³K) und ΔT = {delta_t_simple:.1f} K ergibt sich "
                f"Q ≈ {q_simple_kW*1000:.0f} W."
            )
            st.info("Hinweis: Das ist eine grobe Abschätzung. Für Planung/Anlagenauslegung ist die detaillierte Betrachtung sinnvoll.")

            st.divider()
            with st.expander("Typische Richtwerte (Daumenregeln)"):
                st.write({
                    "Altbau (unsaniert)": "H ≈ 1.0–1.5 W/(m³K)",
                    "Teilsaniert": "H ≈ 0.6–1.0 W/(m³K)",
                    "Neubau": "H ≈ 0.3–0.8 W/(m³K)",
                    "Passivhaus": "H ≈ 0.15–0.25 W/(m³K)",
                })


if __name__ == "__main__":
    main()
