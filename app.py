import streamlit as st
import pandas as pd

st.set_page_config(page_title="Medewerkers Puntensysteem + Wrapped", layout="wide")
st.title("🏆 Medewerkers en Bedrijven Wrapped")

# ------------------------------
# Puntensysteem per actie
# ------------------------------
POINTS_RULES = {
    "open app": 2,
    "User profile click": 3,
    "Company profile click": 3,
    "event detail": 2,
    "event-checkin": 5,
    "call": 3,
    "call mobile": 3,
    "news_item like": 2,
    "news_item like removed": -2,
    "bulletin board item opened": 2,
    "bulletin board item added": 4,
    "AppCMS fixed": 1,
    "AppCMS menu": 1,
    "AppCMS file": 1,
    "AppCMS applink": 1,
    "AppCMS edited": 1,
    "Message": 2,
    "email": 2,
    "visit website": 3,
    "user added": 1,
    "user deleted": 1,
    "user edited": 1,
    "login": 0
}

# ------------------------------
# Upload je logbestand
# ------------------------------
st.header("📂 Upload activiteitenlog (.xlsx)")
uploaded_file = st.file_uploader("Upload Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    # Datum kolom naar datetime
    if 'Datum' in df.columns:
        df['Datum'] = pd.to_datetime(df['Datum'])

    # ------------------------------
    # Max 1 punt per dag voor open app
    # ------------------------------
    df_open_app = df[df['Actie'] == 'open app'].copy()
    if not df_open_app.empty:
        df_open_app['date'] = df_open_app['Datum'].dt.date
        df_open_app = df_open_app.drop_duplicates(subset=['Persoon', 'date'])
        df_open_app['punten'] = 1
    else:
        df_open_app['punten'] = []

    # Overige acties
    other_actions = df[df['Actie'] != 'open app'].copy()
    other_actions['punten'] = other_actions['Actie'].map(POINTS_RULES).fillna(0)

    # Samenvoegen
    df_points = pd.concat([df_open_app, other_actions], ignore_index=True)

    st.subheader("🏅 Punten per medewerker")
    total_points = (df_points
        .groupby("Persoon")["punten"]
        .sum()
        .reset_index()
        .rename(columns={
            "Persoon": "👤 Medewerker",
            "punten": "🏆 Totaal aantal punten"
        })
        .sort_values(by="🏆 Totaal aantal punten", ascending=False)

    st.dataframe(total_points)

    st.subheader("🏢 Punten per bedrijf")
    if 'Bedrijven' in df_points.columns:
        company_points = df_points.groupby("Bedrijven")["punten"].sum().sort_values(ascending=False)
        st.dataframe(company_points)

    # ------------------------------
    # Algemene statistieken
    # ------------------------------
    st.header("📊 Algemene statistieken")

    def top_n_by_action(action, col_detail='Details', n=10, title=None):
        temp = df_points[df_points['Actie'] == action]
        if temp.empty:
            st.write(f"No data for {action}")
            return
        counts = temp.groupby(col_detail).size().sort_values(ascending=False)
        if title:
            st.subheader(title)
        st.dataframe(counts.head(n))

    top_n_by_action('Company profile click', title="🏢 Meest bekeken bedrijven")
    top_n_by_action('event-checkin', title="🎉 Meest bezochte activiteiten")
    top_n_by_action('news_item like', title="👍 Meest gelikete nieuws items")

    # ------------------------------
    # Persoonlijke Wrapped
    # ------------------------------
    st.header("🎁 Persoonlijke Wrapped")
    persoon_input = st.text_input("Typ je naam voor je persoonlijke Wrapped:")

    if persoon_input:
        user_df = df_points[df_points['Persoon'] == persoon_input]

        if user_df.empty:
            st.write("Naam niet gevonden in logbestand")
        else:
            st.subheader(f"📈 {persoon_input}'s Wrapped")

            # Lange streak open app
            if 'open app' in user_df['Actie'].values:
                app_days = user_df[user_df['Actie'] == 'open app']['Datum'].dt.date.drop_duplicates().sort_values()
                streak = 0
                max_streak = 0
                prev_day = None
                for day in app_days:
                    if prev_day and (day - prev_day).days == 1:
                        streak += 1
                    else:
                        streak = 1
                    max_streak = max(max_streak, streak)
                    prev_day = day
            else:
                max_streak = 0

            st.write(
                f"📱 Langste streak app geopend: {max_streak} dagen" if max_streak > 0 else "📱 Oei, je hebt de app nog nooit geopend! Het is gratis hè")

            # Profielen bekeken
            profile_clicks = user_df[user_df['Actie'] == 'User profile click'].shape[0]
            st.write(
                f"👀 Je hebt {profile_clicks} profielen bekeken" if profile_clicks > 0 else "👀 Wist je al dat je profielen kunt bekijken..?")

            # Bedrijven bekeken
            company_clicks = user_df[user_df['Actie'] == 'Company profile click']
            if not company_clicks.empty:
                counts = company_clicks['Details'].value_counts()
                st.write(f"🏢 Je hebt {len(counts)} bedrijven bekeken. Dit waren je favorieten:")
                st.dataframe(counts)
            else:
                st.write("😲 Oei, je hebt nul bedrijven bekeken... Werk je hier eigenlijk wel?")

            # Activiteiten bezocht / bekeken
            events_viewed = user_df[user_df['Actie'] == 'event detail'].shape[0]
            events_checkin = user_df[user_df['Actie'] == 'event-checkin'].shape[0]
            nr_events = df_points[df_points['Actie'] == 'event detail']['Details'].nunique()
            percentage_bekeken = events_viewed / nr_events * 100
            percentage_bezocht = events_checkin / nr_events * 100
            if events_viewed > 0 and events_checkin > 0:
                st.write(f"🎉 Je hebt {events_viewed} activiteiten bekeken en {events_checkin} activiteiten bezocht... Dat is {percentage_bezocht:.0f}% van alle activiteiten 🤓☝️")
            elif events_viewed > 0:
                st.write(f"🎉 Je hebt {events_viewed} activiteiten bekeken! Dat is {percentage_bekeken:.0f}% van alle activiteiten 🤓☝️")
            elif events_checkin > 0:
                st.metric("Activiteiten bezocht", events_checkin)
                st.write(f"🎉 Je hebt {events_checkin} activiteiten bezocht! Dat is {percentage_bezocht:.0f}% van alle activiteiten 🤓☝️")
            else:
                st.write(f"😔 Je hebt nog nooit een activiteit bekeken of bezocht. Kom eens langs; is écht gezellig!")

            # Belletjes
            calls = user_df[user_df['Actie'].isin(['call', 'call mobile'])].shape[0]
            st.write(f"📞 Je pleegde {calls} belletjes via bundeling. Een beller is sneller!" if calls > 0 else "📞 Je hebt (nog) geen belletjes gepleegd via Bundeling, maar nu weet je dat het kan! #EenBellerIsSneller")

            # Likes
            likes = user_df[user_df['Actie'] == 'news_item like'].shape[0]
            st.write(f"👍 Je hebt {likes} nieuws items geliked. Wij vinden jou ook leuk 🫶" if likes > 0 else "👍 Je hebt (nog) geen nieuws items geliked. Vind je ons wel leuk? 😢")
            likes_removed = user_df[user_df['Actie'] == 'news_item like removed'].shape[0]
            if likes_removed > 0:
                st.write(f"👎 Je hebt {likes_removed} keer een like verwijderd... Was de post niet leuk genoeg? 🥺")

            # Prikbord
            bulletin_added = user_df[user_df['Actie'] == 'bulletin board item added'].shape[0]
            if bulletin_added > 0:
                st.write(f"📝 Je hebt {bulletin_added} prikbord items toegevoegd - jeej!")

            # Berichten
            messages = user_df[user_df['Actie'] == 'Message'].shape[0]
            st.write(f"💬 Je hebt {messages} berichten gestuurd via Bundeling! Niet onder werktijd hoop ik... 🫣" if messages > 0 else "💬 Je hebt geen berichten gestuurd via Bundeling - was je hard aan het werk? 😉")
