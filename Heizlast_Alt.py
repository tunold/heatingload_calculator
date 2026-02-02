import math
import streamlit as st


def calculate_heating_demand(volume, heat_loss_factor, delta_t):
    """Berechnet die Heizlast basierend auf dem Gebäudevolumen,
    Wärmeverlustfaktor und Temperaturdifferenz.

    Parameter:
    volume (float): Gebäudevolumen in m³
    heat_loss_factor (float): Wärmeverlustfaktor in W/(m³·K)
    delta_t (float): Temperaturdifferenz in °C

    Returns:
    float: Heizlast in kW
    """
    return volume * heat_loss_factor * delta_t / 1000

def calculate_heating_demand_detailed(length_a, length_b, room_height, number_of_floors,
                                      roof_pitch, first_achse, u_wand, u_roof, u_floor,
                                      infiltration_factor, delta_t, u_window, area_window):
    """
    Berechnet den Wärmeverlust für ein Gebäude mit Satteldach.

    Parameters:
    length_a (float): Länge A
    length_b (float): Länge B
    room_height (float): Raumhöhe
    number_of_floors (int): Anzahl der Stockwerke
    roof_pitch (float): Dachneigung in Grad
    first_achse (str): Welche Achse ist die Firstachse? "A" oder "B"
    u_wand (float): U-Wert der Wand
    u_roof (float): U-Wert des Dachs
    u_floor (float): U-Wert des Bodens
    infiltration_factor (float): Infiltrationsfaktor
    delta_t (float): Temperaturdifferenz

    Returns:
    float: Gesamtwärmeverlust
    """
    # Berechne die Grundfläche
    grundflaeche = length_a * length_b * number_of_floors

    # Berechne die Dachfläche mit dem Dachwinkel
    if first_achse == "A":
        dach_flaeche = (length_b / math.cos(math.radians(roof_pitch))) * length_a
    else:  # "B"
        dach_flaeche = (length_a / math.cos(math.radians(roof_pitch))) * length_b

    # Berechne die Wandfläche (ohne Dachanteile)
    wandflaeche = (length_a + length_b) * room_height * number_of_floors - area_window

    # Berechne die Heizlast
    heat_loss_wand = u_wand * wandflaeche * delta_t/1000.
    heat_loss_roof = u_roof * dach_flaeche * delta_t/1000.
    heat_loss_floor = u_floor * grundflaeche * delta_t /number_of_floors/1000./number_of_floors
    heat_loss_window = u_window * area_window * delta_t/1000.
    heat_loss_infiltration = infiltration_factor * delta_t * grundflaeche/1000.

    heat_loss_hull = heat_loss_wand + heat_loss_roof + heat_loss_floor + heat_loss_window
    total_heat_loss = heat_loss_hull + heat_loss_infiltration

    return total_heat_loss, heat_loss_infiltration, heat_loss_hull, {
        "Grundfläche": grundflaeche,
        "Dachfläche": dach_flaeche,
        "Wandfläche": wandflaeche
    }


# Hauptanwendung
def main():
    # Titel der App
    st.title("Heizlastberechnung für Gebäude")

    # Tabs für die verschiedenen Berechnungsmethoden
    tab1, tab2 = st.tabs(["Detaillierte Berechnung", "Einfache Erfahrungsberechnung"])

    with tab1:
        st.header("Detaillierte Heizlastberechnung")
        st.write("Berechnung basierend auf U-Werten und Flächen")

        # Detaillierte Berechnung mit Formular
        with st.form(key='detailed_form'):
            col1 = st.columns(1)[0]

            col1.write("Raumdimensionen:")
            length_a = col1.slider("Länge A (m)", 2.0, 20.0, 10.0)
            length_b = col1.slider("Länge B (m)", 2.0, 20.0, 5.0)
            room_height = col1.slider("Raumhöhe (m)", 2.0, 10.0, 3.0)
            number_of_floors = col1.slider("Zahl der Stockwerke", 2, 10, 1)
            area_window = col1.slider("Fensterfläche (m2)", 10.0,50.0, 25. ,1. )
            roof_pitch = st.slider("Dachneigung (Grad)", 0.0, 90.0, 30.0)
            first_achse = st.selectbox("Firstachse", ("A", "B"))

            # Berechne Grundfläche und Wandfläche
            grundflaeche = length_a * length_b * number_of_floors
            wandflaeche = (length_a + length_b) * room_height * number_of_floors

            col2 = st.columns(1)[0]
            col2.write("Bauteileigenschaften:")

            # U-Wert Wand mit Expander
            # col2.write("Bauteileigenschaften:")

            # Slider mit Einheit
            u_wand = col2.slider(
                "U-Wert Wand (W/(m²K))",
                min_value=0.1,
                max_value=5.0,
                value=2.0,
                step=0.1,
                help="Wärmeverlust durch Wände"
            )

            # Expander mit Informationen
            with col2.expander("Weitere Informationen zum U-Wert der Wand"):
                st.write("""
                            Der U-Wert (Wärmedurchgangskoeffizient) der Wand beschreibt, wie gut die Wand Wärme abführt.

                            **Typische Werte:**
                            - Alte Gebäude: 0.5 - 3.0 W/(m²K)
                            - Moderne Gebäude: 0.15 - 0.3 W/(m²K) (KfW-70 oder KfW-50)
                            - Passivhäuser: < 0.1 W/(m²K)
                            """)

            # Slider mit Einheit
            u_window = col2.slider(
                "U-Wert Fenster (W/(m²K))",
                min_value=0.1,
                max_value=7.0,
                value=6.0,
                step=0.1,
                help="Wärmeverlust durch Wände"
            )

            # Expander mit Informationen
            with col2.expander("Weitere Informationen zum U-Wert der Fenster"):
                st.write("""
                Der U-Wert (Wärmedurchgangskoeffizient) der Wand beschreibt, wie gut die Wand Wärme abführt.

                **Typische Werte:**
                - Einfachverglasung: 5.0 - 6.0 W/(m²K)
                - 2 fach Verglasung: 1 - 1.3 W/(m²K)
                - 3-fach Verglasung:  0.6 - 9,8 W/(m²K)
                """)

            # U-Wert Dach mit Expander
            u_dach = col2.slider(
                "U-Wert Dach (W/(m²K))",
                min_value=0.1,
                max_value=5.0,
                value=2.0,
                step=0.1,
                help="Wärmeverlust durch Dach"
            )

            with col2.expander("Weitere Informationen zum U-Wert des Dachs"):
                st.write("""
                Der U-Wert des Dachs beschreibt die Wärmeübertragung durch das Dach.

                **Typische Werte:**
                - Alte Gebäude: 0.5 - 3.0 W/(m²K)
                - Moderne Gebäude: 0.15 - 0.3 W/(m²K) (KfW-70 oder KfW-50)
                - Passivhäuser: < 0.1 W/(m²K)
                """)

            # U-Wert Boden mit Expander
            u_boden = col2.slider(
                "U-Wert Boden (W/(m²K))",
                min_value=0.1,
                max_value=5.0,
                value=2.0,
                step=0.1,
                help="Wärmeverlust durch Boden"
            )

            with col2.expander("Weitere Informationen zum U-Wert des Bodens"):
                st.write("""
                Der U-Wert des Bodens beschreibt die Wärmeübertragung durch den Boden.

                **Typische Werte:**
                - Alte Gebäude: 0.5 - 3.0 W/(m²K)
                - Moderne Gebäude: 0.15 - 0.3 W/(m²K) (KfW-70 oder KfW-50)
                - Passivhäuser: < 0.1 W/(m²K)
                """)

            # Erläuterung des Infiltrationsfaktors in der UI

            col3 = st.columns(1)[0]
            col3.write("Weitere Parameter:")

            # Slider mit Einheit
            infiltration_factor = col3.slider(
                "Infiltrationsfaktor (W/(m³·K))",
                min_value=0.01,
                max_value=0.3,
                value=0.25,
                step=0.01,
                help="Beschreibt den Wärmeverlust durch Luftdurchtritt durch die Gebäudehülle"
            )

            # Option 1: Hilfetext direkt unter dem Slider
            with col3.expander("Informationen zum Infiltrationsfaktor"):
                st.write("""
                Der Infiltrationsfaktor beschreibt den Wärmeverlust durch Luftdurchtritt durch die Gebäudehülle.

                **Typische Werte:**
                - Alte Gebäude (Schlechte Dichtigkeit): 0.1 - 0.3 W/(m³·K)
                - Moderne Gebäude (Gute Dichtigkeit): 0.02 - 0.05 W/(m³·K)
                - Passivhäuser (Sehr gute Dichtigkeit): < 0.01 W/(m³·K)
                """)

            delta_t = col3.slider("Temperaturdifferenz (°C)", 5.0, 30.0, 20.0)

            submitted = st.form_submit_button("Heizlast berechnen")

            if submitted:
                # Berechne Gebäudevolumen
                volume = grundflaeche * room_height

                u_values = {"Wand": u_wand, "Dach": u_dach, "Boden": u_boden}
                areas = {"Wand": wandflaeche, "Dach": grundflaeche, "Boden": grundflaeche}

                #heating_demand, q_hull, q_infiltration, q_internal = calculate_heating_demand_detailed(
                #    volume, delta_t, u_values, areas, infiltration_factor
                #)

                total_heat_loss, heat_loss_infiltration, heat_loss_hull, areas = calculate_heating_demand_detailed(
                    length_a, length_b, room_height, number_of_floors,
                    roof_pitch, first_achse, u_wand, u_dach, u_boden,
                    infiltration_factor, delta_t, u_window, area_window
                )

                st.write(f"Grundfläche: {areas['Grundfläche']:.2f} m²")
                st.write(f"Dachfläche: {areas['Dachfläche']:.2f} m²")
                st.write(f"Wandfläche: {areas['Wandfläche']:.2f} m²")
                st.write(f"Gesamtwärmeverlust: {total_heat_loss:.2f} kW")

                # Berechne Wärmeverlust pro m² Grundfläche
                wärmeverlust_pro_m2 = total_heat_loss / grundflaeche

                st.success(f"Gesamtheizlast: {total_heat_loss:.2f} kW")
                st.info(f"Wärmeverlust pro m² Grundfläche: {wärmeverlust_pro_m2:.2f} kW/m²")

                st.subheader("Gebäudemesswerte:")
                st.write(f"Grundfläche: {grundflaeche:.2f} m²")
                st.write(f"Gebäudevolumen: {volume:.2f} m³")
                st.write(f"Wandfläche: {wandflaeche:.2f} m²")
                st.write(f"Zahl der Stockwerke: {number_of_floors}")

                st.subheader("Aufschlüsselung der Heizlast:")
                st.write(f"- Wärmeverlust durch Gebäudehülle: {heat_loss_hull:.2f} kW")
                st.write(f"- Lüftungsverlust: {heat_loss_infiltration:.2f} kW")
                #st.write(f"- Innere Wärmegewinne: {q_internal:.2f} kW")

                st.subheader("Empfehlungen:")
                if heat_loss_hull > 1.0:
                    st.warning("Hoher Wärmeverlust durch Gebäudehülle. Überlegen Sie einer energetischen Sanierung.")
                if infiltration_factor > 3.0:
                    st.warning("Hoher Infiltrationsfaktor. Prüfen Sie die Dichtigkeit des Gebäudes.")

    with tab2:
        st.header("Einfache Erfahrungsberechnung")
        st.write("Berechnung basierend auf Gebäudevolumen und Wärmeverlustfaktor")

        # Eingaben für Grundfläche und Raumhöhe
        col1, col2, col3 = st.columns(3)
        with col1:
            grundflaeche = st.slider("Grundfläche (m²)", 10.0, 500.0, 100.0)
        with col2:
            raumhoehe = st.slider("Raumhöhe (m)", 2.0, 10.0, 3.0)

        # Berechne Gebäudevolumen
        volume_simple = grundflaeche * raumhoehe

        # Einfache Berechnung mit Formular
        with st.form(key='simple_form'):
            col1 = st.columns(1)[0]

            # Wärmeverlustfaktor mit Expander
            heat_loss_factor_simple = col1.slider(
                "Wärmeverlustfaktor (W/m³K)",
                min_value=0.01,
                max_value=2.0,
                value=1.5,
                step=0.1,
                help="Wärmeverlust durch volumetrischen Wärmehaushalt"
            )

            with col1.expander("Weitere Informationen zum Wärmeverlustfaktor"):
                st.write("""
                Der Wärmeverlustfaktor beschreibt den Wärmeverlust pro Raumvolumen und Temperaturdifferenz.

                **Typische Werte:**
                - Alte Gebäude: 1 - 1.5 W/m³K
                - Moderne Gebäude: 0.3- 0.8 W/m³K
                - Passivhäuser: < 0.15 - 0.25 W/m³K

                Erhöhter Wärmeverlust kann auf folgende Faktoren hindeuten:
                - Nicht gedämte Fenster
                - Undichte Gebäudehülle
                - Alte Isolierglasscheiben
                - Ineffiziente Heiztechnik
                """)


            delta_t_simple = col1.slider("Temperaturdifferenz (°C)", 5.0, 30.0, 15.0)

            submitted_simple = st.form_submit_button("Heizlast berechnen")

            if submitted_simple:
                heating_demand_simple = calculate_heating_demand(
                    volume_simple, heat_loss_factor_simple, delta_t_simple
                )

                # Wärmeverlust pro m² Grundfläche
                wärmeverlust_pro_m2 = heating_demand_simple / grundflaeche

                st.success(f"Gesamtheizlast: {heating_demand_simple:.2f} kW")
                st.info(f"Wärmeverlust pro m² Grundfläche: {wärmeverlust_pro_m2:.2f} kW / m2")

                st.write(
                    f"Mit einem Wärmeverlustfaktor von {heat_loss_factor_simple} W/(m³K) und einer Temperaturdifferenz von {delta_t_simple}°C beträgt die Heizlast {heating_demand_simple * 1000:.0f} W.")

                st.write(
                    "Hinweis: Dieser Wert kann als grober Schätzwert für die Heizlast dienen. Eine detaillierte Berechnung sollte für genauere Ergebnisse verwendet werden.")


if __name__ == "__main__":
    main()
