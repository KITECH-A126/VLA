# SmolVLA Simulation Dataset Archive

OpenArm Isaac Lab 시뮬레이션 환경과 scripted IK 데이터 생성 파이프라인을 보존하는 아카이브다.

이 브랜치의 범위는 **환경·데이터 생성 코드·assets·데이터셋 이력 및 검증 정보**다. 용량이 큰 데이터셋 ZIP은 Git에 중복 저장하지 않고 아래 Notion 아카이브에서 관리한다.

## 1. 핵심 산출물

- OpenArm + Tesollo gripper Isaac Lab 환경
- 상단·손목 RGB 2-camera 관측
- scripted IK pick-and-place expert
- 실물 gripper 범위 매핑
- 8-D state/action의 radian→degree 변환
- Red/Blue/Yellow language-conditioned 데이터 생성
- 같은 layout의 세 색이 모두 성공해야 저장하는 atomic triplet
- cube 위치 및 성공·실패 attempt 로그
- pretrained VLM 색 인식 점검 후 적용한 고채도 무광 재질

## 2. 생성 데이터셋 및 다운로드

전체 데이터셋 파일은 [시뮬레이션 데이터셋 모음(Notion)](https://app.notion.com/p/3cfc15950d5180fe8bd1dfcece693a65?source=copy_link)에서 관리한다. GitHub에는 데이터셋 파일을 넣지 않고 생성 코드, 실행 명령과 데이터 설명만 보존한다.

### 2.1 버전별 데이터셋 이력

| 코드 버전 | 데이터셋/배포 위치 | Episodes | 주요 조건 |
|---|---|---:|---|
| ver.1 | `openarm_pick_place_10ep_top.zip` | 10 | 고정 cube, 기본 IK, TCP tilt 45°, top camera |
| ver.2 | Hugging Face `a126-kitech/openarm_dual_realsense_pick_place` | 50 | 고정 cube, TCP tilt 45°, top+wrist cameras |
| ver.3 | `random_cube_tilt_50.zip`; Hugging Face `a126-kitech/openarm_dual_realsense_pick_place_random_tilt` | 50 | X `-0.65~-0.50`, Y `0.02~0.15`, TCP tilt `20~50°`, 2 cameras |
| ver.4 | `random_cube_tilt_30_gripper_mapped_box_red_50.zip` | 50 | X `-0.65~-0.50`, Y `0.02~0.15`, TCP tilt 30°, real-gripper mapping, red box |
| ver.4 | `random_cube_tilt_30_gripper_mapped_box_blue_50.zip` | 50 | 위와 동일, blue box |
| ver.5 | `random_cube_tilt_30_gripper_mapped_box_blue_50_degree.zip` | 50 | ver.4 blue-box 조건 + 8-D state/action degree 변환; single-cube 최종 baseline |
| ver.6 | `openarm_three_color_transit_tilt_50.zip` | 150 (색당 50) | X `-0.62~-0.45`, Y `0.00~0.15`, TCP tilt 50°, blue box, R→B→Y 반복 |
| ver.7 | `openarm_three_color_triplet_tilt50_with_positions.zip` | 150 (색당 50) | X `-0.60~-0.40`, Y `0.00~0.15`, gray box, 동일 layout에서 R·B·Y 모두 성공해야 저장 |
| **ver.7.1 (최종 정본)** | `openarm_three_color_triplet_tilt50_matte.zip` | **150 (색당 50)** | X `-0.59~-0.47`, Y `0.01~0.14`, TCP tilt 50°, gray box, atomic triplet + 고채도 무광 cube |

여기서 `tilt`는 gripper의 열림 각도가 아니라 **pick 접근 시 end-effector/TCP의 기울기**다. `gripper_mapped`는 시뮬레이션 gripper 값을 실제 OpenArm/Tesollo gripper 범위와 맞춘다는 의미다.

### 2.2 최종 재현 대상

| 데이터셋 | Episodes | Frames | FPS | 용도 |
|---|---:|---:|---:|---|
| `random_cube_tilt_30_gripper_mapped_box_blue_50_degree` | 50 | 25,378 | 30 | Single-cube baseline |
| `openarm_three_color_triplet_tilt50_matte` | 150 | 77,160 | 30 | 최종 3색 atomic-triplet |

### 2.3 최종 데이터셋 스키마

ver.5와 ver.7.1 최종 데이터셋은 동일한 LeRobot v3 feature 계약을 사용한다.

| Feature key | dtype / 저장 방식 | Shape | 의미 |
|---|---|---|---|
| `observation.state` | `float32` | `(8,)` | 현재 시뮬레이터에서 측정한 왼팔 7축 joint position과 gripper position |
| `action` | `float32` | `(8,)` | 해당 frame에서 controller가 로봇에 내린 왼팔 7축 joint-position target과 gripper target |
| `observation.images.top` | `video` (기본값) 또는 `image` | `(480, 640, 3)` | 고정된 상단 RealSense 시점의 RGB 영상, 배열 순서는 height × width × channel |
| `observation.images.wrist` | `video` (기본값) 또는 `image` | `(480, 640, 3)` | 손목 장착 RealSense 시점의 RGB 영상, 배열 순서는 height × width × channel |
| `task` | LeRobot task metadata | 문자열 | 각 episode에 대응하는 자연어 instruction |

`observation.state`와 `action`의 8개 원소 순서는 고정이다.

| Index | 이름 | 대상 | 최종 기록 단위 |
|---:|---|---|---|
| 0 | `joint_1` | `openarm_left_joint1` | degree |
| 1 | `joint_2` | `openarm_left_joint2` | degree |
| 2 | `joint_3` | `openarm_left_joint3` | degree |
| 3 | `joint_4` | `openarm_left_joint4` | degree |
| 4 | `joint_5` | `openarm_left_joint5` | degree |
| 5 | `joint_6` | `openarm_left_joint6` | degree |
| 6 | `joint_7` | `openarm_left_joint7` | degree |
| 7 | `gripper` | 실제 gripper 범위로 mapping한 대표 finger command | degree |

시뮬레이션에는 서로 반대 방향으로 움직이는 두 finger joint가 있지만, 실물 인터페이스는 gripper command 하나만 사용하므로 데이터에는 `openarm_left_finger_joint1`에 대응하는 값 하나만 기록한다. index 7의 범위는 simulation의 closed `0 rad` / open `0.044 rad`를 실물 기준 closed `-15°` / open `-60°`로 선형 mapping한 값이다. 이후 8개 값을 모두 degree로 변환해 저장한다.

공통 기록 설정은 다음과 같다.

| 항목 | 값 |
|---|---|
| `robot_type` | `openarm_isaaclab` |
| FPS | 30 |
| 기본 camera 저장 | video (`--use_videos`) |
| camera 수 | 2 (`top`, `wrist`) |
| timestamp | `frame_index / 30`초; `LeRobotDataset.add_frame()`이 생성 |
| episode 저장 조건 | pick-and-place 성공 episode만 최종 dataset에 저장 |

ver.5 single-cube의 기본 task 문자열은 다음과 같다.

```text
Pick up the red cube and place it in the storage box.
```

ver.7.1 three-color dataset은 target color에 따라 다음 세 task를 사용한다.

```text
Pick up the red cube and place it in the storage box.
Pick up the blue cube and place it in the storage box.
Pick up the yellow cube and place it in the storage box.
```

> 버전 주의: 위 degree 스키마는 ver.5 이후의 최종 데이터 기준이다. 기반 코드와 ver.1~4는 실행 옵션 및 wrapper에 따라 radian을 기록할 수 있으므로 단위를 확인하지 않고 함께 사용하지 않는다.

데이터셋 ZIP은 이 Git 브랜치에 포함하지 않는다. 재현 시 위 Notion 페이지에서 필요한 버전의 데이터셋을 내려받는다.

## 3. 코드 발전 과정

| 버전 | 진입 파일 | 변경 내용 |
|---|---|---|
| 1 | `openarm_table_realsense_ik_pick_place_make_dataset.py` | 고정 cube, 기본 IK, 단일 camera |
| 2 | `openarm_table_dual_realsense_ik_pick_place_make_dataset.py` | top+wrist 2 cameras |
| 3 | `openarm_table_dual_realsense_ik_pick_place_make_dataset_random_cube_random_tilt.py` | cube 위치와 TCP tilt 무작위화 |
| 4 | `openarm_table_dual_realsense_ik_pick_place_make_dataset_random_cube_random_tilt_gripper_mapped.py` | 실물 gripper 범위 매핑 |
| 5 | `openarm_table_dual_realsense_ik_pick_place_make_dataset_random_cube_random_tilt_gripper_mapped_degree.py` | state/action degree 변환 |
| 6 | `openarm_table_dual_realsense_ik_pick_place_make_dataset_three_color_random_cube_random_tilt_gripper_mapped_degree.py` | 3색 language-conditioned episode |
| 6.1 | `openarm_three_color_dataset_with_position_logs.py` | cube 위치 로그 추가 |
| 7 | `openarm_three_color_triplet_atomic_dataset_with_positions.py` | 동일 layout atomic triplet |
| 7.1 | `openarm_three_color_triplet_atomic_dataset_with_positions_matte.py` | 고채도 무광 cube 적용 |

최종 정본은 ver.7.1이며 이전 버전은 개발 판단과 데이터 변화의 재현을 위해 보존한다. 모든 코드는 [`scripts/make_dataset`](scripts/make_dataset)에 있다.

### 3.1 파일별 역할

| 파일 | 역할 |
|---|---|
| `openarm_table_realsense_ik_pick_place_make_dataset.py` | ver.1. 단일 상단 camera와 고정 cube의 기본 scripted IK 수집기 |
| `openarm_table_dual_realsense_ik_pick_place_make_dataset.py` | ver.2. top+wrist camera를 함께 기록하는 독립형 수집기 |
| `openarm_table_dual_realsense_ik_pick_place_make_dataset_random_cube.py` | ver.3 이후가 공유하는 기반 환경. cube 위치 sampling, DLS IK, camera, recorder와 state machine 제공 |
| `openarm_table_dual_realsense_ik_pick_place_make_dataset_random_cube_random_tilt.py` | 기반 환경에 episode별 TCP tilt sampling 추가 |
| `openarm_table_dual_realsense_ik_pick_place_make_dataset_random_cube_random_tilt_gripper_mapped.py` | 실제 OpenArm gripper 범위에 맞춘 state/action mapping 추가 |
| `openarm_table_dual_realsense_ik_pick_place_make_dataset_random_cube_random_tilt_gripper_mapped_degree.py` | 기록 직전 7개 joint와 gripper를 radian에서 degree로 변환 |
| `openarm_table_dual_realsense_ik_pick_place_make_dataset_three_color_random_cube_random_tilt_gripper_mapped_degree.py` | 3색 cube, 색상별 instruction, 성공 episode 재시도와 R→B→Y 순서 추가 |
| `openarm_three_color_dataset_with_position_logs.py` | ver.6을 감싸 cube sampled/initial 위치와 attempt 결과 기록 |
| `openarm_three_color_triplet_atomic_dataset_with_positions.py` | 동일 layout의 R/B/Y 세 episode를 atomic하게 수집·병합 |
| `openarm_three_color_triplet_atomic_dataset_with_positions_matte.py` | ver.7의 수집 로직을 재사용하면서 cube의 시각 재질만 무광으로 교체한 최종 진입점 |
| `scripts/inspect_parquet.py` | 생성 후 `tasks.parquet`, episode metadata와 instruction 확인 |

### 3.2 코드 의존 관계

파일명 왼쪽의 설명은 해당 파일을 직접 실행했을 때의 버전이다. 아래에서 `import` 화살표는 위 파일이 아래 파일의 기능을 불러와 확장한다는 뜻이다.

#### 최종 ver.7.1 실행 경로

```text
[ver.7.1 최종 실행 파일]
openarm_three_color_triplet_atomic_dataset_with_positions_matte.py
└─ import → openarm_three_color_triplet_atomic_dataset_with_positions.py
             [ver.7: 동일 layout의 세 색을 atomic하게 수집]
             └─ import → openarm_table_dual_realsense_ik_pick_place_make_dataset_three_color_random_cube_random_tilt_gripper_mapped_degree.py
                          [ver.6: 3색 cube와 색상별 language instruction]
                          └─ import → openarm_table_dual_realsense_ik_pick_place_make_dataset_random_cube_random_tilt_gripper_mapped_degree.py
                                       [ver.5: state/action을 degree로 변환]
                                       └─ import → openarm_table_dual_realsense_ik_pick_place_make_dataset_random_cube_random_tilt_gripper_mapped.py
                                                    [ver.4: 실제 gripper 범위 매핑]
                                                    └─ import → openarm_table_dual_realsense_ik_pick_place_make_dataset_random_cube.py
                                                                 [공통 기반: scene, DLS IK, camera, recorder, state machine]
```

따라서 ver.7.1을 실행하려면 위 여섯 파일이 모두 필요하다. 사용자가 직접 실행하는 파일은 맨 위의 `openarm_three_color_triplet_atomic_dataset_with_positions_matte.py`이고, 나머지는 실행 과정에서 자동으로 import된다.

#### ver.6.1 위치 로그 실행 경로

```text
[ver.6.1 실행 파일]
openarm_three_color_dataset_with_position_logs.py
└─ import → openarm_table_dual_realsense_ik_pick_place_make_dataset_three_color_random_cube_random_tilt_gripper_mapped_degree.py
             └─ import → openarm_table_dual_realsense_ik_pick_place_make_dataset_random_cube_random_tilt_gripper_mapped_degree.py
                          └─ import → openarm_table_dual_realsense_ik_pick_place_make_dataset_random_cube_random_tilt_gripper_mapped.py
                                       └─ import → openarm_table_dual_realsense_ik_pick_place_make_dataset_random_cube.py
```

#### ver.3 random tilt 실행 경로

```text
[ver.3 실행 파일]
openarm_table_dual_realsense_ik_pick_place_make_dataset_random_cube_random_tilt.py
└─ import → openarm_table_dual_realsense_ik_pick_place_make_dataset_random_cube.py
```

#### 독립형 초기 구현

다음 두 파일은 위 상속·import 체인에 포함되지 않는 독립형 초기 수집기다.

```text
[ver.1]
openarm_table_realsense_ik_pick_place_make_dataset.py

[ver.2]
openarm_table_dual_realsense_ik_pick_place_make_dataset.py
```

최종 파일 하나만 따로 복사하면 실행되지 않는다. 파일 누락과 import 오류를 피하려면 `scripts/make_dataset/`의 Python 파일 전체와 `assets/openarm_use/`를 저장소의 현재 디렉터리 구조 그대로 유지한다.

### 3.3 버전별 실행 명령어

모든 명령은 저장소 루트에서 실행한다. 아래 경로의 데이터셋 이름은 새 이름으로 바꿔도 된다. 기존 결과를 삭제할 의도가 확실할 때만 `--overwrite_dataset`을 붙인다.

ver.1 — 고정 cube, 단일 camera:

```bash
/home/zxro/IsaacLab/isaaclab.sh -p \
  scripts/make_dataset/openarm_table_realsense_ik_pick_place_make_dataset.py \
  --num_episodes 10 \
  --dataset_root /home/zxro/outputs/lerobot_datasets/openarm_pick_place_10ep_top
```

ver.2 — 고정 cube, top+wrist cameras:

```bash
/home/zxro/IsaacLab/isaaclab.sh -p \
  scripts/make_dataset/openarm_table_dual_realsense_ik_pick_place_make_dataset.py \
  --num_episodes 50 \
  --dataset_root /home/zxro/outputs/lerobot_datasets/openarm_dual_realsense_pick_place_50
```

ver.3 — random cube와 random TCP tilt:

```bash
/home/zxro/IsaacLab/isaaclab.sh -p \
  scripts/make_dataset/openarm_table_dual_realsense_ik_pick_place_make_dataset_random_cube_random_tilt.py \
  --num_episodes 50 \
  --dataset_root /home/zxro/outputs/lerobot_datasets/random_cube_tilt_50 \
  --cube_x_range -0.65 -0.50 \
  --cube_y_range 0.02 0.15 \
  --tilt_deg_range 20 50 \
  --cube_random_seed 2 \
  --tilt_random_seed 2 \
  --headless
```

ver.4 — 실제 gripper mapping:

```bash
/home/zxro/IsaacLab/isaaclab.sh -p \
  scripts/make_dataset/openarm_table_dual_realsense_ik_pick_place_make_dataset_random_cube_random_tilt_gripper_mapped.py \
  --num_episodes 50 \
  --dataset_root /home/zxro/outputs/lerobot_datasets/random_cube_tilt_30_gripper_mapped \
  --cube_x_range -0.65 -0.50 \
  --cube_y_range 0.02 0.15 \
  --tilt_deg_range 30 30 \
  --headless
```

ver.5 — gripper mapping + degree 변환, 최종 single-cube 데이터:

```bash
/home/zxro/IsaacLab/isaaclab.sh -p \
  scripts/make_dataset/openarm_table_dual_realsense_ik_pick_place_make_dataset_random_cube_random_tilt_gripper_mapped_degree.py \
  --num_episodes 50 \
  --dataset_root /home/zxro/outputs/lerobot_datasets/random_cube_tilt_30_gripper_mapped_box_blue_50_degree \
  --cube_x_range -0.65 -0.50 \
  --cube_y_range 0.02 0.15 \
  --tilt_deg_range 30 30 \
  --cube_random_seed 42 \
  --headless
```

ver.6 — 3색 독립 episode:

```bash
/home/zxro/IsaacLab/isaaclab.sh -p \
  scripts/make_dataset/openarm_table_dual_realsense_ik_pick_place_make_dataset_three_color_random_cube_random_tilt_gripper_mapped_degree.py \
  --num_episodes 50 \
  --dataset_root /home/zxro/outputs/lerobot_datasets/openarm_three_color_transit_tilt_50 \
  --cube_x_range -0.62 -0.45 \
  --cube_y_range 0.00 0.15 \
  --cube_min_separation 0.09 \
  --tilt_deg_range 50 50 \
  --headless
```

ver.6.1 — 3색 + 위치 로그:

```bash
/home/zxro/IsaacLab/isaaclab.sh -p \
  scripts/make_dataset/openarm_three_color_dataset_with_position_logs.py \
  --num_episodes 50 \
  --dataset_root /home/zxro/outputs/lerobot_datasets/openarm_three_color_tilt50_with_positions \
  --cube_x_range -0.60 -0.46 \
  --cube_y_range 0.00 0.15 \
  --cube_z 0.10 \
  --cube_min_separation 0.09 \
  --tilt_deg_range 50 50 \
  --episode_timeout_s 30
```

ver.7 — 동일 layout atomic triplet:

```bash
/home/zxro/IsaacLab/isaaclab.sh -p \
  scripts/make_dataset/openarm_three_color_triplet_atomic_dataset_with_positions.py \
  --num_episodes 50 \
  --dataset_root /home/zxro/outputs/lerobot_datasets/openarm_three_color_triplet_tilt50_with_positions \
  --cube_x_range -0.60 -0.40 \
  --cube_y_range 0.00 0.15 \
  --cube_z 0.10 \
  --cube_min_separation 0.09 \
  --tilt_deg_range 50 50 \
  --episode_timeout_s 35 \
  --ik_failure_timeout_s 5
```

ver.7.1은 5절의 최종 명령어를 사용한다.

### 3.4 파라미터 설명

#### 가장 먼저 알아야 할 규칙

- 거리와 위치 단위는 metre, joint와 action의 최종 기록 단위는 degree다.
- `tilt`는 gripper가 벌어지는 각도가 아니라 **로봇 TCP가 cube에 접근하는 기울기**다.
- X/Y는 Isaac Sim world 좌표계의 table 작업 영역이다.
- `MIN MAX` 형식 옵션은 두 숫자를 공백으로 구분해서 입력한다.
- ver.1~5의 `--num_episodes`는 전체 episode 수다.
- ver.6~7.1의 `--num_episodes`는 **색상별 episode 수 또는 저장할 triplet 수**다. `50`이면 Red/Blue/Yellow 각각 50개, 총 150 episodes가 생성된다.

#### 출력과 실행 옵션

| 파라미터 | 의미 | 사용 예 |
|---|---|---|
| `--dataset_root PATH` | 생성할 LeRobot 데이터셋의 로컬 저장 경로 | `--dataset_root /home/zxro/outputs/lerobot_datasets/my_dataset` |
| `--dataset_repo_id ID` | 데이터셋 metadata에 기록할 식별자. 로컬 전용이면 `local/이름` 권장 | `--dataset_repo_id local/my_dataset` |
| `--num_episodes N` | 생성할 episode 또는 triplet 수. 위의 버전별 규칙에 주의 | `--num_episodes 50` |
| `--task TEXT` | dataset에 기록할 language instruction | `--task "Pick up the red cube and place it in the storage box."` |
| `--headless` | Isaac Sim 화면을 띄우지 않고 실행 | 서버·장시간 수집 시 사용 |
| `--record_camera` / `--no-record_camera` | RGB camera frame 기록 여부 | 최종 데이터는 `--record_camera` 사용 |
| `--use_videos` / `--no-use_videos` | camera frame을 video로 저장할지 개별 image로 저장할지 선택 | 기본값 `--use_videos` |
| `--overwrite_dataset` | 같은 경로의 기존 데이터와 staging을 지우고 새로 생성 | 기존 데이터 보존 시 사용 금지 |
| `--push_to_hub` | 생성 완료 후 Hugging Face Hub로 업로드 | 로컬 보존만 하면 생략 |
| `--private` | Hub 업로드 시 private dataset으로 설정 | `--push_to_hub`와 함께 사용 |

`--overwrite_dataset`은 복구가 어려운 삭제를 수행할 수 있다. 재실행할 때는 기존 경로에 이 옵션을 붙이는 대신 새 `dataset_root`를 지정하는 것이 안전하다.

#### Cube 위치 파라미터

| 파라미터 | 의미 | 최종값 |
|---|---|---:|
| `--cube_x X` | 고정 배치에서 cube 중심의 X 좌표 | 버전별 기본값 사용 |
| `--cube_y Y` | 고정 배치에서 cube 중심의 Y 좌표 | 버전별 기본값 사용 |
| `--cube_z Z` | cube를 떨어뜨려 settle시키는 초기 Z 높이 | `0.10` |
| `--cube_x_range MIN MAX` | episode/layout마다 균일분포로 sampling할 X 범위 | `-0.59 -0.47` |
| `--cube_y_range MIN MAX` | episode/layout마다 균일분포로 sampling할 Y 범위 | `0.01 0.14` |
| `--cube_random_seed N` | 같은 cube 위치 순서를 재현하기 위한 난수 seed | 필요 시 고정 |
| `--cube_min_separation D` | 3색 cube 중심 사이의 최소 XY 거리 | `0.09` |
| `--cube_sampling_max_attempts N` | 충돌 없는 3색 layout을 찾기 위한 최대 sampling 횟수 | 기본값 `1000` |

`cube_min_separation`은 cube가 너무 가까워 서로 충돌하거나 grasp를 방해하는 것을 막는다. 코드가 허용하는 최솟값은 약 `0.0708m`이며 최종 데이터는 여유를 둔 `0.09m`를 사용했다.

#### TCP 자세와 이동 파라미터

| 파라미터 | 의미 | 최종/기본값 |
|---|---|---:|
| `--tilt_deg DEG` | 고정 TCP 접근 기울기 | 기본 `45` |
| `--tilt_deg_range MIN MAX` | episode별 TCP 기울기 sampling 범위. 같은 값을 두 번 주면 고정 | 최종 `50 50` |
| `--tilt_random_seed N` | tilt sampling 순서를 재현하는 seed | 필요 시 고정 |
| `--tilt_at_safe_height` | cube로 이동하기 전 안전 높이에서 tilt를 적용 | 기본 활성화 |
| `--safe_z Z` | cube 사이를 이동할 때 사용하는 안전 높이 | 기본 `0.28` |
| `--pregrasp_clearance D` | cube 바로 위 pre-grasp 지점의 여유 높이 | 기본 `0.05` |
| `--grasp_offset D` | settle된 cube 중심에 더하는 TCP Z offset | 기본 `0.0` |
| `--place_clearance D` | storage box에 놓을 때 사용하는 추가 높이 | 기본 `0.01` |
| `--max_cartesian_step D` | IK 경로 한 step의 최대 직선 이동량 | 기본 `0.008` |
| `--max_rotation_step R` | IK 경로 한 step의 최대 회전량, radian | 기본 `0.035` |

#### 성공 판정과 timeout

| 파라미터 | 의미 | 최종/기본값 |
|---|---|---:|
| `--episode_timeout_s S` | 전체 controller attempt가 이 시간을 넘으면 실패 처리 후 재시도 | 최종 `35` |
| `--settle_failure_timeout_s S` | 초기 cube가 안정되지 않을 때 기다리는 최대 시간 | 기본 `3` |
| `--ik_failure_timeout_s S` | 하강 종료 후 grasp IK가 수렴하기를 기다리는 추가 시간 | 최종 `5` |
| `--grasp_position_tolerance D` | grasp 목표 위치 도달로 인정하는 위치 오차 | 최종 `0.007` |
| `--grasp_rotation_tolerance R` | grasp 목표 회전 도달로 인정하는 오차, radian | 기본 `0.05` |
| `--grasp_reached_hold_s S` | 위치·회전 조건을 연속 유지해야 하는 시간 | 기본 `0.25` |
| `--success_timeout_s S` | 이동 완료 후 cube가 box 안에서 안정되기를 기다리는 시간 | 기본 `2` |
| `--success_hold_time_s S` | box 내부 성공 조건을 연속 유지해야 하는 시간 | 기본 `0.25` |
| `--success_max_linear_speed V` | 성공 판정 시 허용하는 cube 최대 선속도, m/s | 기본 `0.05` |

timeout은 느린 성공을 잘라내는 동시에 수집이 한 episode에서 무한 대기하는 것을 방지한다. 값을 너무 작게 하면 정상 trajectory도 실패로 폐기될 수 있다.

#### 위치 로그와 atomic triplet 옵션

이 기능은 생성 당시의 cube 배치를 나중에 재현하고, 실패 episode의 원인을 사후 확인할 수 있도록 **큐브 위치와 attempt 이력을 별도로 남기기 위해 작성했다.** 위치 정보는 LeRobot frame feature에 추가하지 않고 데이터셋 옆의 JSON/CSV 로그로 저장한다.

| 파라미터 | 적용 버전 | 의미 |
|---|---|---|
| `--position_log_dir PATH` | ver.6.1~7.1 | cube 위치와 attempt JSON/CSV를 저장할 경로. 생략하면 `DATASET_ROOT_cube_positions` |
| `--overwrite_position_logs` | ver.6.1~7.1 | 기존 위치 로그만 지우고 다시 기록 |
| `--keep_triplet_staging` | ver.7~7.1 | 최종 병합 후에도 색상별 임시 triplet dataset을 보존 |

ver.7~7.1은 `DATASET_ROOT_triplet_staging`에 임시 episode를 만들고, 동일 layout의 세 색이 모두 성공했을 때만 최종 데이터셋으로 병합한다. 중간 디버깅이 필요하지 않다면 staging은 최종 병합 후 제거하는 기본 동작을 사용한다.

기본 로그 구조는 다음과 같다.

```text
DATASET_ROOT_cube_positions/
├── manifest.json
├── triplets.csv
├── saved_episodes.csv
└── attempts/attempt_XXXXXX.json
```

최종 데이터의 실제 sampled 범위는 X `-0.589884...~-0.470105...`, Y `0.010078...~0.139903...`로 명령의 설정 범위와 일치한다.

#### 생성 결과 확인

Task instruction과 episode metadata를 확인한다.

```bash
python3 scripts/inspect_parquet.py \
  /home/zxro/outputs/lerobot_datasets/DATASET_NAME/meta/tasks.parquet \
  --commands-only
```

기본 metadata 수치를 확인한다.

```bash
python3 -c 'import json; p="/home/zxro/outputs/lerobot_datasets/DATASET_NAME/meta/info.json"; d=json.load(open(p)); print("episodes=", d["total_episodes"], "frames=", d["total_frames"], "fps=", d["fps"])'
```

## 4. 최종 atomic-triplet 방식

```text
3색 cube layout 무작위 생성
  → 같은 layout 복원 후 Red instruction 수행
  → 같은 layout 복원 후 Blue instruction 수행
  → 같은 layout 복원 후 Yellow instruction 수행
  → 세 episode가 모두 성공하면 triplet 저장
  → 하나라도 실패하면 세 episode 전체 폐기
```

초기에는 episode마다 layout을 다시 생성했지만, 색상별 장면 분포가 달라 language 효과가 layout 차이에 묻힐 수 있었다. triplet 방식은 동일한 시각 조건에서 instruction만 바꾸기 위한 설계다.

## 5. 최종 데이터 생성 명령어

```bash
/home/zxro/IsaacLab/isaaclab.sh -p \
  scripts/make_dataset/openarm_three_color_triplet_atomic_dataset_with_positions_matte.py \
  --num_episodes 50 \
  --dataset_root /home/zxro/outputs/lerobot_datasets/openarm_three_color_triplet_tilt50_matte_new \
  --dataset_repo_id local/openarm_three_color_triplet_tilt50_matte_new \
  --cube_x_range -0.59 -0.47 \
  --cube_y_range 0.01 0.14 \
  --cube_z 0.10 \
  --cube_min_separation 0.09 \
  --tilt_deg_range 50 50 \
  --episode_timeout_s 35 \
  --ik_failure_timeout_s 5 \
  --grasp_position_tolerance 0.007 \
  --device cuda:1
```

`--num_episodes 50`은 50 successful triplets, 즉 Red 50 + Blue 50 + Yellow 50 = 총 150 episodes를 뜻한다. 기존 결과를 삭제할 의도가 확실할 때만 `--overwrite_dataset`을 추가한다.

생성 당시 manifest의 repo ID는 `a126-kitech/openarm_pick_place`였지만 로컬 재현에서는 의미가 분명한 `local/...` label을 사용한다. 데이터 내용에는 영향을 주지 않는다.

## 6. 무광 재질 발견 경위

3색 데이터 구조를 개선한 뒤에도 색 구분이 불안정하여 pretrained VLM이 simulation RGB에서 cube 색을 구분하는지 확인했다. 기존 재질은 조명 반사와 표면 highlight 때문에 고유 색 특징이 약해졌다. 무광 재질에서 색 구분이 상대적으로 개선되어 다음 설정을 최종 환경에 적용했다.

```text
Red:    (1.00, 0.01, 0.01)
Blue:   (0.01, 0.08, 1.00)
Yellow: (1.00, 0.95, 0.01)
emissive: false
roughness: 1.0
metallic: 0.0
opacity: 1.0
```

질량, 마찰, damping, collision, IK trajectory와 camera 조건은 유지해 시각 재질만 변경했다. 이 관찰은 실물 데모에서 링라이트 조도를 낮춘 뒤 Demo 1이 0/2에서 2/2로 바뀐 현상과 같은 메커니즘을 지지한다.

## 7. 개발환경과 assets

### 7.1 개발환경

Isaac Sim, Isaac Lab, LeRobot 설치와 개발환경 구성은 [개발환경 정리(Notion)](https://app.notion.com/p/380c15950d5180d999e6ce076d038dd8?source=copy_link)를 참고한다.

### 7.2 Assets

시뮬레이션 실행에 필요한 OpenArm, Tesollo gripper, RealSense camera, table, storage box와 texture는 `assets/openarm_use/`에 정리되어 있다.

USD 파일들이 폴더 내부의 다른 USD와 texture를 상대 경로로 참조하므로 `assets/openarm_use/` 전체 구조를 유지해야 한다. 일부 파일만 따로 복사하거나 폴더 구조를 변경하면 참조가 끊겨 scene 또는 robot asset이 정상적으로 열리지 않을 수 있다.

## 8. 최종 아카이빙 구조와 담당 범위

### 8.1 GitHub에 보존하는 내용

GitHub 정본은 `KITECH-A126/VLA` 저장소의 `smolvla-simulation-dataset` 브랜치다. 코드 리뷰와 재현에 필요한 작은 파일만 commit한다.

| 경로 | 내용 | 담당 |
|---|---|---|
| `README.md` | 환경, 데이터 이력·스키마, 코드 관계, 전체 생성 명령, 파라미터, 무광 재질 발견 경위 | 김수경 |
| `scripts/make_dataset/` | ver.1~7.1 데이터 생성 코드; 파일명과 import 구조를 그대로 유지 | 김수경 |
| `scripts/inspect_parquet.py` | 생성 데이터의 episode/task metadata 확인 도구 | 김수경 |
| `assets/openarm_use/` | OpenArm, gripper, camera, table, storage box와 texture USD assets | 김수경 |

데이터셋 ZIP은 용량이 크므로 이 브랜치에 commit하지 않고 Notion에서 관리한다.

### 8.2 Notion에 보존하는 내용

[시뮬레이션 데이터셋 모음(Notion)](https://app.notion.com/p/3cfc15950d5180fe8bd1dfcece693a65?source=copy_link)은 binary artifact의 다운로드 정본이다.

| Notion 항목 | 반드시 포함할 내용 |
|---|---|
| 버전별 데이터셋 | ver.1~7.1 ZIP 또는 Hugging Face 위치, 대응 생성 코드명, episode 수, cube 범위, TCP tilt, camera 수, box 색상, 단위 |
| Single-cube 최종 데이터 | `random_cube_tilt_30_gripper_mapped_box_blue_50_degree.zip`; 50 episodes, 25,378 frames, 30 FPS |
| Three-color 최종 데이터 | `openarm_three_color_triplet_tilt50_matte.zip`; 150 episodes, 77,160 frames, 30 FPS |
| 데이터 생성 근거 | 사용한 전체 명령어와 Git commit/branch, 생성 날짜, 개발환경 Notion 링크 |
| 위치 로그 | ver.6.1~7.1의 manifest, triplet, saved-episode, attempt log 파일 |
| 데이터 주의사항 | state/action 8-D 순서와 degree 단위, gripper mapping, atomic-triplet 조건, 무광 재질 적용 여부 |

Notion에 파일을 첨부할 때는 이름만 적지 않고 실제 다운로드가 가능한지 다른 팀원 계정으로 확인한다. 외부 Hugging Face dataset은 repo ID뿐 아니라 클릭 가능한 주소와 private 접근 방법을 함께 기록한다.
