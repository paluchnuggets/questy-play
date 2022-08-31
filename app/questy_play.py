import random

import numpy as np
import streamlit as st
from deta import Deta
from PIL import Image


def disable_other_checkboxes(*other_checkboxes_keys):
    for checkbox_key in other_checkboxes_keys:
        st.session_state[checkbox_key] = False


def download_img_from_deta(large_file, path: str):
    with open(path, "wb+") as f:
        for chunk in large_file.iter_chunks(4096):
            f.write(chunk)
        large_file.close()


@st.cache
def shuffle_questions(questions):
    random.shuffle(questions)
    return questions


params = st.experimental_get_query_params()

if question_id_list := params.get("question_id"):
    question_id = question_id_list[0]

    # Set up Deta store
    deta = Deta(st.secrets["deta_key"])
    db = deta.Base("example-db")
    photos = deta.Drive("photos")

    data = db.get(key=question_id)

    questions = data["misleading_answers"] + [data["answer"]]
    questions = shuffle_questions(questions=questions)

    # Set up quiz
    st.write("Answer question to get the reward")
    st.write(data["question"])

    option_1 = st.checkbox(
        questions[0],
        key="op1",
        on_change=disable_other_checkboxes,
        args=("op2", "op3", "op4"),
    )
    option_2 = st.checkbox(
        questions[1],
        key="op2",
        on_change=disable_other_checkboxes,
        args=("op1", "op3", "op4"),
    )
    option_3 = st.checkbox(
        questions[2],
        key="op3",
        on_change=disable_other_checkboxes,
        args=("op2", "op1", "op4"),
    )
    option_4 = st.checkbox(
        questions[3],
        key="op4",
        on_change=disable_other_checkboxes,
        args=("op2", "op3", "op1"),
    )

    answers_indicators = [option_1, option_2, option_3, option_4]
    correct_answer_idx = np.where(answers_indicators)
    correct_answer_dx_len = len(correct_answer_idx[0])

    if correct_answer_dx_len == 0:
        st.write("Choose your answer!")

    if correct_answer_dx_len == 1:
        if questions[correct_answer_idx[0][0]] == data["answer"]:

            download_reward_img_path = f"./data/downloaded_{data['id']}_reward.png"
            drive_reward_img_body = photos.get(data["reward_image_name"])

            download_img_from_deta(
                large_file=drive_reward_img_body, path=download_reward_img_path
            )
            reward_image = Image.open(download_reward_img_path)

            st.image(reward_image, caption="Reward image")
        else:
            st.write("Wrong answer, sorry :(")
