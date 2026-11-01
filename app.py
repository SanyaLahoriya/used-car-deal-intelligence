
import streamlit as st

st.set_page_config(
    page_title="Used Car Deal Intelligence",
    page_icon="🚗",
    layout="wide"
)

st.title("🚗 Used Car Deal Intelligence")

st.write(
    "Evaluate used-car listings and compare "
    "seller asking prices with estimated market prices."
)

st.info(
    "Application setup complete. "
    "Machine learning model integration is pending."
)

st.divider()

st.header("Enter Vehicle Details")

with st.form("car_form"):

    car_name = st.text_input(
        "Car Make, Model and Variant",
        placeholder="e.g. Hyundai Creta SX"
    )

    col1, col2 = st.columns(2)

    with col1:
        year = st.number_input(
            "Manufacturing Year",
            min_value=1980,
            max_value=2026,
            value=2020
        )

    with col2:
        km_driven = st.number_input(
            "Kilometres Driven",
            min_value=0,
            value=50000,
            step=1000
        )

    listed_price = st.number_input(
        "Seller Asking Price (₹ Lakhs)",
        min_value=0.01,
        value=5.0,
        step=0.1
    )

    submitted = st.form_submit_button(
        "Evaluate Listing",
        use_container_width=True
    )

if submitted:

    st.success("Vehicle details submitted successfully!")

    st.subheader("Your Submitted Details")

    st.write("Car:", car_name)
    st.write("Year:", year)
    st.write("Kilometres Driven:", km_driven)
    st.write("Asking Price:", listed_price, "Lakh")

    st.warning(
        "Price prediction will be available "
        "after connecting the trained ML model."
    )
