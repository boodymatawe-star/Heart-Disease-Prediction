from datetime import date

import streamlit as st

from database import (
    create_patient,
    delete_patient,
    get_all_patients,
    get_patient,
    get_patient_predictions,
    search_patients,
    update_patient,
)

user      = st.session_state.user
doctor_id = user["id"]

st.title("👥 Patient Management")
st.markdown("---")

tab_list, tab_add = st.tabs(["📋  Patient List", "➕  Add New Patient"])

# ── Patient List ───────────────────────────────────────────────────────────────
with tab_list:
    search_query = st.text_input(
        "🔍 Search by name or National ID",
        placeholder="Start typing to filter…",
    )
    patients = (
        search_patients(search_query, doctor_id)
        if search_query
        else get_all_patients(doctor_id)
    )

    if not patients:
        st.info("No patients found. Register your first patient in the **Add New Patient** tab.")
    else:
        st.markdown(f"**{len(patients)} patient(s)**")

        for p in patients:
            p_id     = p["id"]
            is_edit  = st.session_state.get("editing_patient_id") == p_id
            dob_str  = p.get("date_of_birth") or "N/A"
            gender   = p.get("gender") or "N/A"
            label    = f"🧑‍⚕️ {p['full_name']}  —  {gender}  |  DOB: {dob_str}"

            with st.expander(label, expanded=is_edit):

                # ── View mode ──────────────────────────────────────────────────
                if not is_edit:
                    d1, d2, d3 = st.columns(3)
                    with d1:
                        st.markdown(f"**National ID:** {p.get('national_id') or 'N/A'}")
                        st.markdown(f"**Phone:** {p.get('phone') or 'N/A'}")
                        st.markdown(f"**Email:** {p.get('email') or 'N/A'}")
                    with d2:
                        st.markdown(f"**Address:** {p.get('address') or 'N/A'}")
                        st.markdown(f"**Emergency Contact:** {p.get('emergency_contact') or 'N/A'}")
                        st.markdown(f"**Registered:** {(p.get('created_at') or '')[:10]}")
                    with d3:
                        preds    = get_patient_predictions(p_id)
                        positive = sum(1 for x in preds if x["result"] == 1)
                        st.metric("Predictions", len(preds))
                        st.metric("Positive",    positive)
                        st.metric("Negative",    len(preds) - positive)

                    if p.get("medical_notes"):
                        st.markdown(f"**Medical Notes:** {p['medical_notes']}")

                    btn1, btn2, _ = st.columns([1, 1, 4])
                    with btn1:
                        if st.button("✏️ Edit", key=f"edit_btn_{p_id}"):
                            st.session_state["editing_patient_id"] = p_id
                            st.rerun()
                    with btn2:
                        if st.button("🗑️ Delete", key=f"del_btn_{p_id}"):
                            st.session_state["confirm_delete"] = p_id

                    # Inline delete confirmation
                    if st.session_state.get("confirm_delete") == p_id:
                        st.warning(
                            f"Delete **{p['full_name']}** and all their prediction records?"
                        )
                        yes_col, no_col = st.columns(2)
                        with yes_col:
                            if st.button("Yes, delete", key=f"yes_{p_id}", type="primary"):
                                delete_patient(p_id)
                                st.session_state.pop("confirm_delete", None)
                                st.success("Patient deleted.")
                                st.rerun()
                        with no_col:
                            if st.button("Cancel", key=f"cancel_{p_id}"):
                                st.session_state.pop("confirm_delete", None)
                                st.rerun()

                # ── Edit mode ──────────────────────────────────────────────────
                else:
                    with st.form(f"edit_form_{p_id}"):
                        e1, e2 = st.columns(2)
                        with e1:
                            e_name      = st.text_input("Full Name *",         value=p["full_name"])
                            e_nid       = st.text_input("National ID",          value=p.get("national_id") or "")
                            e_dob       = st.text_input("Date of Birth (YYYY-MM-DD)", value=p.get("date_of_birth") or "")
                            e_gender    = st.selectbox(
                                "Gender", ["Male", "Female"],
                                index=0 if p.get("gender") == "Male" else 1,
                            )
                        with e2:
                            e_phone     = st.text_input("Phone",               value=p.get("phone") or "")
                            e_email     = st.text_input("Email",               value=p.get("email") or "")
                            e_emergency = st.text_input("Emergency Contact",   value=p.get("emergency_contact") or "")
                            e_address   = st.text_area("Address",              value=p.get("address") or "", height=80)
                        e_notes = st.text_area("Medical Notes",                value=p.get("medical_notes") or "", height=80)

                        save_btn, cancel_btn = st.columns(2)
                        with save_btn:
                            saved = st.form_submit_button("💾 Save Changes", type="primary", use_container_width=True)
                        with cancel_btn:
                            cancelled = st.form_submit_button("Cancel", use_container_width=True)

                        if saved:
                            if not e_name:
                                st.error("Full name is required.")
                            else:
                                update_patient(
                                    p_id, e_nid or None, e_name, e_dob, e_gender,
                                    e_phone, e_email, e_address, e_emergency, e_notes,
                                )
                                st.session_state.pop("editing_patient_id", None)
                                st.success("Patient updated successfully.")
                                st.rerun()
                        if cancelled:
                            st.session_state.pop("editing_patient_id", None)
                            st.rerun()


# ── Add New Patient ────────────────────────────────────────────────────────────
with tab_add:
    st.subheader("➕ Register New Patient")

    with st.form("add_patient_form", clear_on_submit=True):
        a1, a2 = st.columns(2)
        with a1:
            a_name      = st.text_input("Full Name *")
            a_nid       = st.text_input("National ID", help="Must be unique if provided")
            a_dob       = st.date_input("Date of Birth", value=date(1970, 1, 1))
            a_gender    = st.selectbox("Gender *", ["Male", "Female"])
        with a2:
            a_phone     = st.text_input("Phone Number")
            a_email     = st.text_input("Email Address")
            a_emergency = st.text_input("Emergency Contact (name & phone)")
            a_address   = st.text_area("Address", height=80)

        a_notes = st.text_area("Medical Notes / Allergies / Chronic Conditions", height=90)

        submitted = st.form_submit_button(
            "➕ Register Patient", type="primary", use_container_width=True
        )

        if submitted:
            if not a_name:
                st.error("Full name is required.")
            else:
                pid, err = create_patient(
                    a_nid or None, a_name, str(a_dob), a_gender,
                    a_phone, a_email, a_address, a_emergency, a_notes, doctor_id,
                )
                if err:
                    st.error(err)
                else:
                    st.success(f"✅ Patient **{a_name}** registered successfully (ID: {pid}).")
