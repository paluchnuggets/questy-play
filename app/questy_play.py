import random

import numpy as np
import streamlit as st
from deta import Deta
from PIL import Image
from PIL.PngImagePlugin import PngImageFile


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


@st.cache
def download_and_show_image(id: str, image_name: str) -> PngImageFile:
    download_question_img_path = f"./data/downloaded_{id}_question.png"
    drive_question_img_body = photos.get(image_name)
    download_img_from_deta(
        large_file=drive_question_img_body, path=download_question_img_path
    )
    question_image = Image.open(download_question_img_path)
    return question_image


def set_up_Deta(base_name: str, drive_name: str):
    deta = Deta(st.secrets["deta_key"])
    db = deta.Base(base_name)
    photos = deta.Drive(drive_name)
    return db, photos


@st.cache
def get_data_from_Deta_base(key: str):
    return db.get(key=key)


params = st.experimental_get_query_params()

if question_id_list := params.get("question_id"):
    question_id = question_id_list[0]

    # Set up Deta store
    db, photos = set_up_Deta(base_name="example-db", drive_name="photos")

    data = get_data_from_Deta_base(key=question_id)

    questions = data["misleading_answers"] + [data["answer"]]
    questions = shuffle_questions(questions=questions)

    # Set up quiz
    st.header(data["question"])

    if data["question_image_name"]:
        question_image = download_and_show_image(
            id=data["id"], image_name=data["question_image_name"]
        )
        st.image(question_image, caption="")

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

    if correct_answer_dx_len == 1:
        if questions[correct_answer_idx[0][0]] == data["answer"]:
            st.success("Correct answer :)")
            st.balloons()

            with st.spinner("Wait for reward image..."):
                download_reward_img_path = f"./data/downloaded_{data['id']}_reward.png"
                drive_reward_img_body = photos.get(data["reward_image_name"])
                download_img_from_deta(
                    large_file=drive_reward_img_body, path=download_reward_img_path
                )
                reward_image = Image.open(download_reward_img_path)
                st.image(reward_image, caption=data["reward_photo_description"])
        else:
            st.info("Wrong answer, sorry :(")
