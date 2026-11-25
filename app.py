import streamlit as st
import joblib
import pandas as pd
from pathlib import Path
from risk_engine import assess_ownership_risk

# ---------------------------------------------------------
# Page setup and model loading
# ---------------------------------------------------------
st.set_page_config(
    page_title="Used Car Deal Intelligence",
    page_icon="🚗",
    layout="wide"
)

MODEL_PATH = Path(__file__).parent / "price_pipeline.joblib"


@st.cache_resource
def load_model():
    """Load the saved preprocessing + Random Forest pipeline once."""
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "price_pipeline.joblib was not found. "
            "Place it in the same folder as app.py."
        )
    return joblib.load(MODEL_PATH)


st.title("🚗 Used Car Deal Intelligence")
st.write(
    "Evaluate a used-car listing by comparing the seller's asking price "
    "with the model's estimated market price."
)

try:
    model = load_model()
    st.success("Trained price prediction model loaded successfully.")
except Exception as exc:
    st.error(f"Could not load the trained model: {exc}")
    st.stop()

st.divider()

# ---------------------------------------------------------
# Fuel type is outside the form so the E20 field can appear
# dynamically when Petrol is selected.
# ---------------------------------------------------------
st.header("Enter Vehicle Details")
st.caption(
    "Fields marked * are mandatory. Other vehicle details are optional. "
    "Optional details can improve the completeness of the evaluation."
)

fuel_options = [
    "Not specified",
    "Petrol",
    "Diesel",
    "CNG",
    "LPG",
    "Electric",
    "Hybrid",
    "Other",
]

fuel = st.selectbox(
    "Fuel type (optional)",
    options=fuel_options,
    index=0,
    help="Select Petrol to provide E20 compatibility information for the risk engine."
)

is_petrol = fuel.strip().lower() == "petrol"

with st.form("car_form"):
    st.subheader("Required details")
    col1, col2 = st.columns(2)

    with col1:
        make = st.text_input("Car make *", placeholder="e.g. Hyundai")
        manufacturing_year = st.number_input(
            "Manufacturing year *",
            min_value=1980,
            max_value=2026,
            value=2020,
            step=1
        )
        km_driven = st.number_input(
            "Kilometres driven *",
            min_value=0,
            value=50000,
            step=1000
        )

    with col2:
        model_name = st.text_input("Car model *", placeholder="e.g. Creta")
        asking_price = st.number_input(
            "Seller asking price (₹ lakhs) *",
            min_value=0.01,
            value=5.0,
            step=0.1
        )

    # E20 compatibility is collected only for petrol vehicles.
    # It is kept separate from model_input and is NOT sent to price prediction.
    e20_compatibility = None
    if is_petrol:
        st.divider()
        st.subheader("Risk engine details")
        e20_compatibility = st.selectbox(
            "Is this petrol vehicle E20 compatible?",
            options=["Not sure", "Yes", "No"],
            index=0,
            help=(
                "This answer is reserved for the vehicle risk engine. "
                "It is not used by the price prediction model."
            )
        )

    st.divider()
    st.subheader("Additional vehicle details (optional)")
    st.caption("Leave any field blank if you don't know the information.")

    col1, col2, col3 = st.columns(3)

    with col1:
        variant = st.text_input("Variant", placeholder="e.g. SX")
        engine_cc_text = st.text_input(
            "Engine capacity (cc)", placeholder="e.g. 1497"
        )

    with col2:
        seating_text = st.text_input(
            "Seating capacity", placeholder="e.g. 5"
        )
        gearbox_type = st.text_input(
            "Gearbox / transmission", placeholder="e.g. Manual"
        )

    with col3:
        owners = st.text_input(
            "Ownership", placeholder="e.g. First Owner"
        )
        has_insurance = st.text_input(
            "Has insurance?", placeholder="e.g. Yes"
        )
        induction = st.text_input(
            "Induction type", placeholder="e.g. Naturally Aspirated"
        )

    submitted = st.form_submit_button(
        "Evaluate Listing",
        use_container_width=True
    )


# ---------------------------------------------------------
# Prediction and deal analysis
# ---------------------------------------------------------
if submitted:
    errors = []

    if not make.strip():
        errors.append("Car make")
    if not model_name.strip():
        errors.append("Car model")
    if asking_price <= 0:
        errors.append("A valid asking price")

    def optional_number(value, field_label):
        """Convert an optional numeric field; blank values remain missing."""
        value = value.strip()
        if value == "":
            return None
        try:
            return float(value)
        except ValueError:
            errors.append(f"A valid number for {field_label}")
            return None

    engine_cc = optional_number(engine_cc_text, "engine capacity")
    seating_capacity = optional_number(seating_text, "seating capacity")

    if errors:
        st.error("Please provide: " + ", ".join(errors) + ".")
    else:
        # PRICE MODEL INPUT:
        # Keep these 12 features aligned with train.py.
        # E20 compatibility and asking price are deliberately excluded.
        model_input = pd.DataFrame([{
            "make": make.strip(),
            "model": model_name.strip(),
            "year": int(manufacturing_year),
            "engine_cc": engine_cc,
            "seating_capacity": seating_capacity,
            "gearbox_type": gearbox_type.strip() or None,
            "fuel": None if fuel == "Not specified" else fuel,
            "owners": owners.strip() or None,
            "km_driven": int(km_driven),
            "has_insurance": has_insurance.strip() or None,
            "induction": induction.strip() or None,
            "variant": variant.strip() or None,
        }])

        # RISK ENGINE INPUT:
        # This is separate from model_input and is not passed to model.predict().
        risk_engine_input = {
            "year": int(manufacturing_year),
            "km_driven": int(km_driven),
            "owners": owners,
            "gearbox_type": gearbox_type,
            "fuel": fuel,
            "induction": induction,
            "e20_compatibility": e20_compatibility if is_petrol else None,
            "has_insurance": has_insurance,
        }

        st.divider()
        st.header("Ownership Risk Assessment")
        risk = assess_ownership_risk(**risk_engine_input)
        c1, c2 = st.columns(2)
        c1.metric("Indicative risk score", f"{risk['score']}/100")
        c2.metric("Weighted information coverage", f"{risk['coverage']}%")
        st.progress(risk['score'] / 100)
        if risk['coverage'] < 70:
            st.warning("Limited information — risk category withheld.")
        else:
            st.write(f"**Indicative category:** {risk['category']} Risk")
        if risk['unknowns']:
            st.warning("Unassessed factors: " + ", ".join(risk['unknowns']))
        if is_petrol and e20_compatibility == "No":
            st.warning("Reported E20 incompatibility. Verify approved fuel with the manufacturer before purchase.")
        st.dataframe(pd.DataFrame(risk['breakdown']), use_container_width=True, hide_index=True)
        st.caption("Heuristic screening of known factors, not a failure probability. Accident history, service history and actual mechanical condition are not assessed. Obtain an independent inspection.")

        try:
            predicted_price = float(model.predict(model_input)[0])
            asking = float(asking_price)

            if predicted_price <= 0:
                st.error(
                    "The model returned a non-positive price. "
                    "Please check the vehicle details and training data."
                )
                st.stop()

            difference = asking - predicted_price
            difference_pct = (difference / predicted_price) * 100

            st.divider()
            st.header("Deal Intelligence Results")

            metric1, metric2, metric3 = st.columns(3)
            metric1.metric(
                "Estimated market price",
                f"₹{predicted_price:.2f} lakh"
            )
            metric2.metric(
                "Seller asking price",
                f"₹{asking:.2f} lakh"
            )
            metric3.metric(
                "Asking price vs estimate",
                f"{difference_pct:+.1f}%",
                delta=f"₹{difference:+.2f} lakh",
                delta_color="inverse"
            )

            # Transparent app-side rule; not a separate ML classifier.
            if asking < predicted_price * 0.90:
                st.success(
                    "🟢 Potentially Good Deal — the asking price is more than "
                    "10% below the model's estimated price."
                )
                suggested_action = (
                    "The asking price is below the model estimate. "
                    "Still verify the car's condition, documents and history."
                )
            elif asking > predicted_price * 1.10:
                st.error(
                    "🔴 Potentially Overpriced — the asking price is more than "
                    "10% above the model's estimated price."
                )
                suggested_action = (
                    f"Consider discussing a price closer to the estimated "
                    f"market price of ₹{predicted_price:.2f} lakh, subject to "
                    "vehicle condition and local comparable listings."
                )
            else:
                st.info(
                    "🟡 Fairly Priced — the asking price is within 10% "
                    "of the model's estimated price."
                )
                suggested_action = (
                    "The asking price is broadly close to the model estimate. "
                    "Use inspection findings and comparable listings to negotiate."
                )

            st.subheader("Negotiation insight")
            st.write(suggested_action)

            lower_reference = predicted_price * 0.95
            upper_reference = predicted_price * 1.05
            st.write(
                f"**Indicative comparison range (±5% of model estimate):** "
                f"₹{lower_reference:.2f}–₹{upper_reference:.2f} lakh"
            )
            st.caption(
                "This is a simple reference range around the model estimate, "
                "not a statistically validated confidence interval or guaranteed "
                "negotiation price."
            )

            with st.expander("View the details sent to the price model"):
                st.dataframe(model_input, use_container_width=True)
                st.caption(
                    "E20 compatibility is intentionally not included in this table "
                    "or in the price prediction model."
                )

            with st.expander("View the separate risk-engine inputs"):
                st.json(risk_engine_input)
                st.caption(
                    "These values are collected separately for the risk engine. "
                    "They are not passed to the price prediction pipeline."
                )

            st.warning(
                "The model estimates price from its training data. It does not "
                "independently assess accident history, mechanical condition, "
                "ownership-document authenticity or inspection risk. Check these "
                "before making a purchase."
            )

        except Exception as exc:
            st.error(f"Prediction failed: {exc}")
            st.info(
                "The saved model expects the same feature names and compatible "
                "data types used during training. Check the model file and "
                "scikit-learn version if this error continues."
            )

st.divider()
st.caption(
    "Used Car Deal Intelligence | ML-based price estimate for decision support"
)