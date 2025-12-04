import streamlit as st
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt

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

    # ------------------------------
    # Punten per medewerker
    # ------------------------------
    st.subheader("🏅 Punten per medewerker")
    total_points = df_points.groupby("Persoon")["punten"].sum().reset_index()
    total_points = total_points.rename(columns={
        "Persoon": "👤 Medewerker",
        "punten": "🏆 Totaal aantal punten"
    }).sort_values(by="🏆 Totaal aantal punten", ascending=False)

    # Ranking toevoegen
    total_points.insert(0, "🏅 Ranking", range(1, len(total_points) + 1))

    # Visualisatie: punten per medewerker
    fig_points = px.bar(total_points,
                        x="👤 Medewerker",
                        y="🏆 Totaal aantal punten",
                        orientation='v',
                        text="🏆 Totaal aantal punten")
    st.plotly_chart(fig_points, use_container_width=True)

    st.dataframe(total_points)

    # ------------------------------
    # Punten per bedrijf (pie chart)
    # ------------------------------
    st.subheader("🏢 Punten per bedrijf")
    if 'Bedrijven' in df_points.columns:
        company_points = (
            df_points.groupby("Bedrijven")["punten"]
            .sum()
            .reset_index()
            .rename(columns={
                "Bedrijven": "🏢 Bedrijf",
                "punten": "🏆 Totaal aantal punten"
            })
            .sort_values(by="🏆 Totaal aantal punten", ascending=False)
            .reset_index(drop=True)
        )

        fig_company = px.pie(company_points,
                             names='🏢 Bedrijf',
                             values='🏆 Totaal aantal punten')
        st.plotly_chart(fig_company, use_container_width=True)

        st.dataframe(company_points)

    # ------------------------------
    # Meest bekeken bedrijven (bar chart)
    # ------------------------------
    st.subheader("🏢 Meest bekeken bedrijven")
    company_views = df_points[df_points['Actie'] == 'Company profile click']
    if not company_views.empty:
        counts = company_views['Details'].value_counts().reset_index()
        counts.columns = ['🏢 Bedrijf', 'Aantal keer bekeken']
        fig = px.bar(counts.head(10), x='🏢 Bedrijf', y='Aantal keer bekeken', orientation='v', text='Aantal keer bekeken')
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(counts.head(10))

    # ------------------------------
    # Meest bezochte activiteiten (wordcloud)
    # ------------------------------
    st.subheader("🎉 Meest bezochte activiteiten")
    events_checkin = df_points[df_points['Actie'] == 'event-checkin']
    if not events_checkin.empty:
        top_events = events_checkin['Details'].value_counts().head(10).reset_index()
        top_events.columns = ['🎉 Activiteit', 'Aantal aanwezigen']
        freq_dict = dict(zip(top_events['🎉 Activiteit'], top_events['Aantal aanwezigen']))
        wordcloud = WordCloud(width=800, height=400, background_color='white')
        wordcloud.generate_from_frequencies(freq_dict)
        plt.figure(figsize=(10, 5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        st.pyplot(plt)
        st.dataframe(top_events)

    # ------------------------------
    # App opens per dag (lijnplot)
    # ------------------------------
    st.subheader("📱 App opens per dag")
    app_opens = df_points[df_points['Actie'] == 'open app'].copy()
    if not app_opens.empty:
        daily_opens = app_opens.groupby(app_opens['Datum'].dt.date).size().reset_index(name='Aantal opens')
        fig = px.line(daily_opens, x='Datum', y='Aantal opens', markers=True)
        st.plotly_chart(fig, use_container_width=True)

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
                counts = company_clicks['Details'].value_counts().reset_index()
                counts.columns = ['🏢 Bedrijf', 'Aantal keer bekeken']
                st.write(f"🏢 Je hebt {len(counts)} bedrijven bekeken. Dit waren je favorieten:")
                top3 = counts.head(3)
                fig_top3 = px.bar(top3, x='🏢 Bedrijf', y='Aantal keer bekeken', orientation='v', text='Aantal keer bekeken')
                st.plotly_chart(fig_top3, use_container_width=True)
            else:
                st.write("😲 Oei, je hebt nul bedrijven bekeken... Werk je hier eigenlijk wel?")

            # Activiteiten bezocht / bekeken
            events_viewed = user_df[user_df['Actie'] == 'event detail'].shape[0]
            events_checkin = user_df[user_df['Actie'] == 'event-checkin'].shape[0]
            nr_events = df_points[df_points['Actie'] == 'event detail']['Details'].nunique()

            race_df = pd.DataFrame({
                '': ['Totaal aantal activiteiten', 'Bekeken door jou', 'Bezocht door jou'],
                'Aantal': [nr_events, events_viewed, events_checkin]
            })

            fig_race = px.bar(race_df, x='Aantal', y='', orientation='h', text='Aantal',
                              title="🎯 Activiteiten race")
            st.plotly_chart(fig_race, use_container_width=True)

            percentage_bekeken = events_viewed / nr_events * 100
            percentage_bezocht = events_checkin / nr_events * 100
            if events_viewed > 0 and events_checkin > 0:
                st.write(f"🎉 Je hebt {events_viewed} activiteiten bekeken en {events_checkin} activiteiten bezocht... Dat is {percentage_bezocht:.0f}% van alle activiteiten 🤓☝️")
            elif events_viewed > 0:
                st.write(f"🎉 Je hebt {events_viewed} activiteiten bekeken! Dat is {percentage_bekeken:.0f}% van alle activiteiten 🤓☝️")
            elif events_checkin > 0:
                st.write(f"🎉 Je hebt {events_checkin} activiteiten bezocht! Dat is {percentage_bezocht:.0f}% van alle activiteiten 🤓☝️")
            else:
                st.write(f"😔 Je hebt nog nooit een activiteit bekeken of bezocht. Kom eens langs; is écht gezellig!")

            # Likes
            likes = user_df[user_df['Actie'] == 'news_item like'].shape[0]
            likes_removed = user_df[user_df['Actie'] == 'news_item like removed'].shape[0]

            likes_df = pd.DataFrame({
                'Type': ['Likes gegeven', 'Likes verwijderd'],
                'Aantal': [likes, likes_removed]
            })

            fig_likes = px.bar(likes_df, x='Type', y='Aantal', text='Aantal', title="👍 Likes")
            st.plotly_chart(fig_likes, use_container_width=True)

            st.write(f"👍 Je hebt {likes} nieuws items geliked. Wij vinden jou ook leuk 🫶" if likes > 0 else "👍 Je hebt (nog) geen nieuws items geliked. Vind je ons wel leuk? 😢")
            if likes_removed > 0:
                st.write(f"👎 Je hebt {likes_removed} keer een like verwijderd... Was de post niet leuk genoeg? 🥺")

            # Belletjes / Berichten / Prikbord
            calls = user_df[user_df['Actie'].isin(['call', 'call mobile'])].shape[0]
            messages = user_df[user_df['Actie'] == 'Message'].shape[0]
            bulletin_added = user_df[user_df['Actie'] == 'bulletin board item added'].shape[0]

            comm_df = pd.DataFrame({
                '': ['📞 Belletjes', '💬 Berichten', '📝 Prikbord items'],
                'Aantal': [calls, messages, bulletin_added]
            })

            fig_comm = px.bar(comm_df, x='', y='Aantal', orientation='v', text='Aantal',
                              title="📊 Communicatie")
            st.plotly_chart(fig_comm, use_container_width=True)

            st.write(f"📞 Je pleegde {calls} belletjes via bundeling. Een beller is sneller!" if calls > 0 else "📞 Je hebt (nog) geen belletjes gepleegd via Bundeling, maar nu weet je dat het kan! #EenBellerIsSneller")
            st.write(f"💬 Je hebt {messages} berichten gestuurd via Bundeling! Niet onder werktijd hoop ik... 🫣" if messages > 0 else "💬 Je hebt geen berichten gestuurd via Bundeling - was je hard aan het werk? 😉")
            if bulletin_added > 0:
                st.write(f"📝 Je hebt {bulletin_added} prikbord items toegevoegd - jeej!")
