
        percentage = probability * 100


        if percentage >= 70:

            risk = "HIGH"

        elif percentage >= 40:

            risk = "MEDIUM"

        else:

            risk = "LOW"


        p1, p2 = st.columns([2, 1])

        with p1:

            st.write(
                f"**Latitude:** {lat:.6f}"
            )

            st.write(
                f"**Longitude:** {lon:.6f}"
            )

            st.write(
                f"**Date:** "
                f"{selected_date.strftime('%d %B %Y')}"
            )

            st.write(
                f"**Horizon:** {horizon}"
            )

            st.progress(
                min(int(percentage), 100)
            )

            st.metric(
                "Estimated Flood Probability",
                f"{percentage:.1f}%"
            )

        with p2:

            if risk == "HIGH":

                st.error(
                    "⚠️ HIGH FLOOD RISK"
                )

            elif risk == "MEDIUM":

                st.warning(
                    "🟠 MEDIUM FLOOD RISK"
                )

            else:

                st.success(
                    "✅ LOW FLOOD RISK"
                )


    else:

        st.info(
            "Forecast data is ready. "
            "Adjust the conditions if needed, "
            "then run the prediction."
        )


    # -----------------------------------------------------
    # Data source
    # -----------------------------------------------------

    st.markdown("---")

    st.header("📡 Data Source")

    st.write(
        "Open-Meteo Forecast API"
    )

    st.write(
        f"Latitude: {lat:.6f}"
    )

    st.write(
        f"Longitude: {lon:.6f}"
    )

    st.link_button(
        "Open Open-Meteo",
        "https://open-meteo.com/",
        use_container_width=True
    )


else:

    st.warning(
        "No forecast data was returned for this date."
    )


# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------

st.markdown("---")

st.caption(
    "NEXUS-Manipur | Phase 1 Future Prediction Prototype"
)