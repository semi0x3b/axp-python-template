class SuccessResponseMessage:
    """API 응답용 표준 성공 메시지"""

    CREATED = "등록되었습니다."
    SAVED = "저장되었습니다."
    UPDATED = "수정되었습니다."
    DELETED = "삭제되었습니다."
    SENT = "전송되었습니다."
    CANCELLED = "취소되었습니다."
    GET = "조회되었습니다."
    SUBMITTED = "제출되었습니다."

    BATCH_CREATED = "일괄 등록되었습니다."
    BATCH_UPDATED = "일괄 수정되었습니다."
    BATCH_DELETED = "일괄 삭제되었습니다."

    NO_SEARCH_RESULTS = "검색된 결과가 없습니다."

    EXECUTED = "실행되었습니다."
    CONFIRMED = "확정되었습니다."

    BLOCKED = "사용자를 차단했습니다."
    UNBLOCKED = "차단이 해제되었습니다."


class ErrorResponseMessage:
    """에러 응답 메시지 (ERR-xxxx 형식의 에러코드 + 메시지)"""

    # 1000번대: 기본 작업 실패
    CREATE_FAILED = {
        "code": "ERR-1001",
        "message": "등록에 실패했습니다. 시스템 관리자에게 문의해주세요.",
    }
    SAVE_FAILED = {
        "code": "ERR-1002",
        "message": "저장에 실패했습니다. 시스템 관리자에게 문의해주세요.",
    }
    UPDATE_FAILED = {
        "code": "ERR-1003",
        "message": "수정에 실패했습니다. 시스템 관리자에게 문의해주세요.",
    }
    DELETE_FAILED = {
        "code": "ERR-1004",
        "message": "삭제에 실패했습니다. 시스템 관리자에게 문의해주세요.",
    }
    GET_FAILED = {
        "code": "ERR-1008",
        "message": "조회에 실패했습니다. 시스템 관리자에게 문의해주세요.",
    }

    # 1100번대: 시스템 오류
    TEMPORARY_ERROR = {
        "code": "ERR-1101",
        "message": "일시적인 오류로 요청사항을 수행하지 못했습니다. 잠시 후 다시 시도해주세요.",
    }
    DATABASE_ERROR = {
        "code": "ERR-1103",
        "message": "데이터베이스 오류가 발생했습니다. 시스템 관리자에게 문의해주세요.",
    }
    REQUEST_VALIDATION_ERROR = {
        "code": "ERR-1104",
        "message": "입력 정보를 다시 확인해주세요.",
    }
    UNKNOWN_ERROR = {
        "code": "ERR-1105",
        "message": "서버 오류가 발생했습니다. 시스템 관리자에게 문의해주세요.",
    }
    PYDANTIC_VALIDATION_ERROR = {
        "code": "ERR-1106",
        "message": "응답 데이터 검증에 실패했습니다. 시스템 관리자에게 문의해주세요.",
    }

    # 1200번대: 데이터 관련
    NO_DATA_FOUND = {"code": "ERR-1201", "message": "등록된 정보가 없습니다."}
    ALREADY_EXISTS = {"code": "ERR-1202", "message": "이미 등록된 항목입니다."}

    # 2000번대: 인증/인가
    UNAUTHORIZED = {"code": "ERR-2001", "message": "인증이 필요합니다."}
    FORBIDDEN = {"code": "ERR-2002", "message": "접근 권한이 없습니다."}
    TOKEN_EXPIRED = {"code": "ERR-2003", "message": "로그인이 만료되었습니다. 다시 로그인해주세요."}
    INVALID_TOKEN = {"code": "ERR-2004", "message": "유효하지 않은 인증 토큰입니다."}
    ACCOUNT_SUSPENDED = {"code": "ERR-2005", "message": "정지된 계정입니다."}
    ACCOUNT_WITHDRAWN = {"code": "ERR-2006", "message": "탈퇴한 계정입니다."}
    ACCOUNT_BANNED = {"code": "ERR-2007", "message": "영구 정지된 계정입니다. 재가입이 불가합니다."}
    ACCOUNT_PENDING = {"code": "ERR-2008", "message": "가입 승인 대기 중입니다."}
    INVALID_CREDENTIALS = {"code": "ERR-2010", "message": "이메일 또는 비밀번호가 올바르지 않습니다."}
    EMAIL_ALREADY_EXISTS = {"code": "ERR-2011", "message": "이미 가입된 이메일입니다."}
    PHONE_ALREADY_EXISTS = {"code": "ERR-2012", "message": "이미 가입된 전화번호입니다."}
    SMS_RATE_LIMIT_EXCEEDED = {
        "code": "ERR-2013",
        "message": "SMS 인증 요청 횟수를 초과했습니다. 1시간 후 다시 시도해주세요.",
    }
    SMS_COOLDOWN_NOT_EXPIRED = {"code": "ERR-2013-1", "message": "잠시 후 다시 시도해주세요. (60초 이내 재발송 불가)"}
    SMS_CODE_EXPIRED = {"code": "ERR-2014", "message": "인증코드가 만료되었습니다."}
    SMS_CODE_INVALID = {"code": "ERR-2015", "message": "인증코드가 올바르지 않습니다."}
    SMS_MAX_ATTEMPTS_EXCEEDED = {
        "code": "ERR-2016",
        "message": "인증코드 확인 횟수를 초과했습니다. 새 코드를 요청해주세요.",
    }
    PHONE_NOT_VERIFIED = {"code": "ERR-2017", "message": "전화번호 인증이 완료되지 않았습니다."}
    UNIVERSITY_NOT_FOUND = {"code": "ERR-2018", "message": "존재하지 않는 대학입니다."}

    # 2019~: 가입 승인/프로필
    PENDING_USER_NOT_FOUND = {"code": "ERR-2019", "message": "대기 중인 회원을 찾을 수 없습니다."}
    ALREADY_APPROVED = {"code": "ERR-2020", "message": "이미 승인된 회원입니다."}
    APPROVAL_PERMISSION_DENIED = {"code": "ERR-2021", "message": "같은 대학의 운영자만 승인할 수 있습니다."}
    NICKNAME_CHANGE_TOO_SOON = {
        "code": "ERR-2022",
        "message": "닉네임은 월 1회만 변경할 수 있습니다. 다음 달 1일부터 변경 가능합니다.",
    }
    INVALID_CURRENT_PASSWORD = {"code": "ERR-2023", "message": "현재 비밀번호가 올바르지 않습니다."}
    PASSWORD_RESET_TOKEN_INVALID = {"code": "ERR-2033", "message": "유효하지 않거나 만료된 비밀번호 재설정 링크입니다."}
    FILE_UPLOAD_NOT_FOUND = {"code": "ERR-2025", "message": "파일을 찾을 수 없습니다."}
    FILE_UPLOAD_OWNER_MISMATCH = {"code": "ERR-2026", "message": "본인이 업로드한 파일만 사용할 수 있습니다."}
    FILE_UPLOAD_TYPE_MISMATCH = {"code": "ERR-2027", "message": "프로필 이미지 파일이 아닙니다."}
    SMS_CODE_ALREADY_USED = {"code": "ERR-2028", "message": "이미 사용된 인증코드입니다. 새 코드를 요청해주세요."}
    WITHDRAWAL_CONFIRMATION_REQUIRED = {"code": "ERR-2024", "message": "탈퇴 확인이 필요합니다."}
    SIGNUP_BANNED = {"code": "ERR-2029", "message": "가입이 제한된 사용자입니다."}
    NICKNAME_CONTAINS_FORBIDDEN_WORD = {"code": "ERR-2030", "message": "닉네임에 사용할 수 없는 단어가 포함되어 있습니다."}
    PROFILE_POPUP_LOGIN_REQUIRED = {"code": "ERR-2031", "message": "프로필 팝업은 회원만 이용할 수 있습니다."}
    PROFILE_POPUP_PENDING = {"code": "ERR-2032", "message": "가입 승인 후 프로필 팝업을 이용할 수 있습니다."}

    # 3000번대: 게시글
    POST_NOT_FOUND = {"code": "ERR-3001", "message": "게시글을 찾을 수 없습니다."}
    SELF_UPVOTE_NOT_ALLOWED = {"code": "ERR-3002", "message": "본인 게시물에는 좋아요할 수 없습니다."}
    SAME_UNIVERSITY_UPVOTE_NOT_ALLOWED = {"code": "ERR-3002-1", "message": "같은 학교 대회 제출물에는 추천할 수 없습니다."}
    COMPETITION_UPVOTE_LIMIT = {"code": "ERR-3002-2", "message": "이미 이 대회의 다른 제출물에 좋아요 했습니다. 취소 후 다시 시도해주세요."}
    POST_NOT_AUTHOR = {"code": "ERR-3003", "message": "게시글 작성자만 수정할 수 있습니다."}
    POST_ALREADY_BLINDED = {"code": "ERR-3004", "message": "블라인드 처리된 게시글입니다."}
    POST_EDIT_NOT_ALLOWED = {"code": "ERR-3005", "message": "삭제되거나 블라인드된 게시글은 수정할 수 없습니다."}
    POST_ALREADY_DELETED = {"code": "ERR-3006", "message": "이미 삭제된 게시글입니다."}
    POST_DELETE_DENIED = {"code": "ERR-3007", "message": "게시글 삭제 권한이 없습니다."}
    POST_WRITE_DENIED = {"code": "ERR-3008", "message": "해당 메뉴에 글을 작성할 권한이 없습니다."}
    NOTICE_WRITE_DENIED = {"code": "ERR-3009", "message": "공지 게시판에는 운영진 이상만 작성할 수 있습니다."}

    # 3010번대: 메뉴
    MENU_NOT_FOUND = {"code": "ERR-3010", "message": "메뉴를 찾을 수 없습니다."}
    MENU_GROUP_NOT_FOUND = {"code": "ERR-3011", "message": "메뉴 그룹을 찾을 수 없습니다."}
    MENU_ACCESS_DENIED = {"code": "ERR-3012", "message": "해당 메뉴에 접근 권한이 없습니다."}
    # 3020번대: 댓글
    COMMENT_NOT_FOUND = {"code": "ERR-3020", "message": "댓글을 찾을 수 없습니다."}
    COMMENT_NOT_AUTHOR = {"code": "ERR-3021", "message": "댓글 작성자만 삭제할 수 있습니다."}
    COMMENT_DEPTH_EXCEEDED = {"code": "ERR-3022", "message": "대댓글에는 답글을 달 수 없습니다."}
    COMMENT_NOT_ALLOWED = {"code": "ERR-3023", "message": "댓글이 허용되지 않는 메뉴입니다."}

    # 3030번대: 신고
    COMPLAINT_DUPLICATE = {"code": "ERR-3030", "message": "이미 신고한 대상입니다."}
    COMPLAINT_SELF_NOT_ALLOWED = {"code": "ERR-3031", "message": "본인 콘텐츠는 신고할 수 없습니다."}
    COMPLAINT_TARGET_NOT_FOUND = {"code": "ERR-3032", "message": "신고 대상을 찾을 수 없습니다."}

    # 3060번대: 블라인드 관리
    BLIND_NOT_BLINDED = {"code": "ERR-3060", "message": "블라인드 상태가 아닌 콘텐츠입니다."}
    BLIND_PERMISSION_DENIED = {"code": "ERR-3061", "message": "같은 대학 콘텐츠만 관리할 수 있습니다."}
    BLIND_INVALID_STATUS = {"code": "ERR-3062", "message": "허용되지 않은 상태값입니다."}

    # 3070번대: 제재
    PENALTY_SELF_NOT_ALLOWED = {"code": "ERR-3070", "message": "본인에게 제재를 부여할 수 없습니다."}
    PENALTY_PERMISSION_DENIED = {"code": "ERR-3071", "message": "같은 대학 회원에게만 제재를 부여할 수 있습니다."}
    PENALTY_USER_NOT_FOUND = {"code": "ERR-3072", "message": "제재 대상 회원을 찾을 수 없습니다."}
    PENALTY_NOT_FOUND = {"code": "ERR-3073", "message": "제재 이력을 찾을 수 없습니다."}
    PENALTY_ALREADY_REVOKED = {"code": "ERR-3074", "message": "이미 해제된 제재입니다."}

    # 3040번대: 게시글 비즈니스 규칙
    COMPETITION_SUMMARY_REQUIRED = {"code": "ERR-3041", "message": "대회 게시판에서는 요약이 필수입니다."}
    COMPETITION_IMAGE_REQUIRED = {"code": "ERR-3042", "message": "대회 게시판에서는 이미지가 1~5장 필요합니다."}
    IMAGE_LIMIT_EXCEEDED = {"code": "ERR-3043", "message": "이미지는 최대 3장까지 첨부할 수 있습니다."}
    COMPETITION_DETAIL_REQUIRED = {"code": "ERR-3044", "message": "대회 게시판에서는 competition_project가 필수입니다."}
    ANONYMOUS_NOT_ALLOWED = {"code": "ERR-3045", "message": "이 게시판은 익명 게시를 허용하지 않습니다."}
    POST_RATE_LIMIT_EXCEEDED = {
        "code": "ERR-3046",
        "message": "게시글 작성 횟수를 초과했습니다. 잠시 후 다시 시도해주세요.",
    }
    POST_COMMENTS_LOCKED = {"code": "ERR-3047", "message": "댓글이 잠긴 게시글입니다."}
    CONTENT_CONTAINS_FORBIDDEN_WORD = {"code": "ERR-3048", "message": "사용할 수 없는 단어가 포함되어 있습니다."}
    COMPETITION_DETAIL_NOT_ALLOWED = {"code": "ERR-3048", "message": "대회 게시판이 아닌 메뉴에서는 competition_project를 사용할 수 없습니다."}
    FILE_EXTENSION_NOT_ALLOWED = {"code": "ERR-3049", "message": "허용되지 않은 파일 확장자입니다."}
    NICKNAME_ALREADY_EXISTS = {"code": "ERR-3050", "message": "이미 사용 중인 닉네임입니다."}
    COMPETITION_USE_DEDICATED_API = {"code": "ERR-3051", "message": "대회 게시판은 전용 API를 사용해주세요."}
    COMPETITION_LABEL_REQUIRED = {"code": "ERR-3052", "message": "대회 게시판에서는 '프로젝트' 또는 '해커톤' 라벨 중 하나를 선택해야 합니다."}
    INVALID_LABEL = {"code": "ERR-3053", "message": "허용되지 않은 라벨이 포함되어 있습니다."}
    SINGLE_LABEL_ONLY = {"code": "ERR-3054", "message": "이 게시판에서는 라벨을 하나만 선택할 수 있습니다."}

    # 3050번대: 좋아요
    SELF_COMMENT_UPVOTE_NOT_ALLOWED = {"code": "ERR-3053", "message": "본인 댓글에는 좋아요할 수 없습니다."}
    COMMENT_UPVOTE_TARGET_NOT_FOUND = {"code": "ERR-3054", "message": "좋아요 대상 댓글을 찾을 수 없습니다."}
    OFFICIAL_MENU_ADMIN_ONLY = {"code": "ERR-3055", "message": "공식 게시판은 관리자만 작성/수정/삭제할 수 있습니다."}
    HOF_READ_ONLY = {"code": "ERR-3056", "message": "명예의전당은 읽기 전용입니다."}
    COMPETITION_PHASE_EDIT_DENIED = {"code": "ERR-3057", "message": "현재 단계에서는 대회 제출물을 수정할 수 없습니다."}
    HOF_NOT_FOUND = {"code": "ERR-3058", "message": "명예의 전당 항목을 찾을 수 없습니다."}
    HOF_ANONYMOUS_NOT_ALLOWED = {"code": "ERR-3059", "message": "대회 제출물은 익명으로 작성할 수 없습니다."}
    HOF_EDITED_ITEMS_EXIST = {"code": "ERR-3060", "message": "관리자가 수정한 항목이 존재합니다. 재생성하려면 force=true로 요청해주세요."}
    HOF_NO_SUBMISSIONS = {"code": "ERR-3061", "message": "해당 대회에 스냅샷할 제출물이 없습니다."}
    TOO_MANY_LABELS = {"code": "ERR-3062", "message": "라벨은 최대 3개까지 선택할 수 있습니다."}

    # 3080번대: 일괄 복제
    BULK_COPY_NO_TARGET_MENU = {"code": "ERR-3080", "message": "일괄 복제 대상 메뉴가 없습니다."}
    BULK_COPY_COMPETITION_POST_NOT_ALLOWED = {"code": "ERR-3082", "message": "대회 게시글은 일괄 복제할 수 없습니다."}

    # 4000번대: 채팅
    CHAT_SELF_CONVERSATION = {"code": "ERR-4001", "message": "자기 자신과 대화할 수 없습니다."}
    CHAT_CONVERSATION_NOT_FOUND = {"code": "ERR-4002", "message": "대화를 찾을 수 없습니다."}
    CHAT_NOT_PARTICIPANT = {"code": "ERR-4003", "message": "대화 참여자가 아닙니다."}
    CHAT_BLOCKED_BY_COUNTERPART = {"code": "ERR-4004", "message": "상대방에 의해 차단되었습니다."}
    CHAT_COMPLAINT_DUPLICATE = {"code": "ERR-4005", "message": "이미 신고한 대상입니다."}
    CHAT_FORBIDDEN_WORD = {"code": "ERR-4006", "message": "메시지에 사용할 수 없는 단어가 포함되어 있습니다."}
    CHAT_BLOCKED = {"code": "ERR-4007", "message": "차단한 상대에게 메시지를 보낼 수 없습니다."}
    CHAT_TARGET_USER_NOT_FOUND = {"code": "ERR-4008", "message": "대화 상대방을 찾을 수 없습니다."}
    CHAT_MESSAGE_NOT_FOUND = {"code": "ERR-4009", "message": "메시지를 찾을 수 없습니다."}
    CHAT_MESSAGE_NOT_SENDER = {"code": "ERR-4030", "message": "본인이 보낸 메시지만 삭제할 수 있습니다."}
    CHAT_BOT_NOT_ALLOWED = {"code": "ERR-4040", "message": "알림봇 계정에는 메시지를 보낼 수 없습니다."}

    # 4031~: 모임 리그 검증
    GATHERING_CREATOR_CANNOT_APPLY = {"code": "ERR-4031", "message": "대회 팀 개설자는 다른 팀에 지원할 수 없습니다."}
    GATHERING_ALREADY_APPROVED_IN_LEAGUE = {"code": "ERR-4032", "message": "이미 참여 중인 팀이 있습니다."}
    GATHERING_PENDING_IN_OTHER_TEAM = {"code": "ERR-4037", "message": "다른 팀에 신청 대기 중인 상태에서는 팀을 개설할 수 없습니다."}

    # 4033~: 모임 개설자 권한 위임
    GATHERING_DELEGATION_ALREADY_PENDING = {"code": "ERR-4033", "message": "이미 진행 중인 위임 요청이 있습니다."}
    GATHERING_DELEGATION_NOT_MEMBER = {"code": "ERR-4034", "message": "승인된 팀원에게만 위임할 수 있습니다."}
    GATHERING_DELEGATION_NOT_FOUND = {"code": "ERR-4035", "message": "위임 요청이 없습니다."}
    GATHERING_DELEGATION_NOT_TARGET = {"code": "ERR-4036", "message": "위임 대상이 아닙니다."}

    # 4010~: 그룹 채팅
    CHAT_GROUP_MAX_PARTICIPANTS = {"code": "ERR-4010", "message": "그룹 채팅은 최대 10명까지 참여할 수 있습니다."}
    CHAT_GROUP_MIN_PARTICIPANTS = {"code": "ERR-4011", "message": "그룹 채팅은 최소 3명이 필요합니다."}
    CHAT_GROUP_NOT_OWNER = {"code": "ERR-4012", "message": "방장만 수행할 수 있는 작업입니다."}
    CHAT_GROUP_OWNER_CANNOT_BE_KICKED = {"code": "ERR-4013", "message": "방장은 강퇴할 수 없습니다."}
    CHAT_GROUP_ALREADY_PARTICIPANT = {"code": "ERR-4014", "message": "이미 참여 중인 사용자가 포함되어 있습니다."}
    CHAT_GROUP_CANNOT_LEAVE_DIRECT = {"code": "ERR-4015", "message": "1:1 대화에서는 퇴장할 수 없습니다."}
    CHAT_GROUP_TITLE_TOO_LONG = {"code": "ERR-4016", "message": "그룹 이름은 50자를 초과할 수 없습니다."}

    # 4020~: 사용자 차단
    CHAT_BLOCK_SELF = {"code": "ERR-4020", "message": "자기 자신을 차단할 수 없습니다."}
    CHAT_BLOCK_ALREADY_EXISTS = {"code": "ERR-4021", "message": "이미 차단된 사용자입니다."}
    CHAT_BLOCK_NOT_FOUND = {"code": "ERR-4022", "message": "차단되지 않은 사용자입니다."}

    # ──────────────────────────────────────────────
    # 5000번대: Backoffice 전용
    # ──────────────────────────────────────────────

    # 5001~5005: 관리자
    ADMIN_NOT_FOUND = {"code": "ERR-5001", "message": "관리자를 찾을 수 없습니다."}
    ADMIN_EMAIL_DUPLICATE = {"code": "ERR-5002", "message": "이미 등록된 관리자 이메일입니다."}
    ADMIN_INVALID_CREDENTIALS = {"code": "ERR-5003", "message": "이메일 또는 비밀번호가 올바르지 않습니다."}
    ADMIN_DELETED = {"code": "ERR-5004", "message": "삭제된 관리자 계정입니다."}
    ADMIN_SELF_DELETE = {"code": "ERR-5005", "message": "본인 계정은 삭제할 수 없습니다."}

    # 5101~5103: 회원 관리
    BO_USER_NOT_FOUND = {"code": "ERR-5101", "message": "회원을 찾을 수 없습니다."}
    BO_USER_ALREADY_SUSPENDED = {"code": "ERR-5102", "message": "이미 정지된 회원입니다."}
    BO_USER_NOT_SUSPENDED = {"code": "ERR-5103", "message": "정지 상태가 아닌 회원입니다."}

    BO_USER_EMAIL_DUPLICATE = {"code": "ERR-5109", "message": "이미 사용 중인 이메일입니다."}
    BO_USER_PHONE_DUPLICATE = {"code": "ERR-5112", "message": "이미 사용 중인 휴대폰번호입니다."}
    BO_USER_BULK_EMPTY = {"code": "ERR-5111", "message": "대상 회원을 찾을 수 없습니다."}
    BO_WITHDRAWN_USER_NOT_FOUND = {"code": "ERR-5110", "message": "탈퇴한 회원을 찾을 수 없습니다."}

    # 5104~5106: 영구 정지/정지 이력
    BO_USER_ALREADY_BANNED = {"code": "ERR-5104", "message": "이미 영구 정지된 회원입니다."}
    BO_USER_NOT_BANNED = {"code": "ERR-5105", "message": "영구 정지 상태가 아닌 회원입니다."}
    BO_PENALTY_NOT_FOUND = {"code": "ERR-5106", "message": "정지 이력 항목을 찾을 수 없습니다."}

    # 5201~5202: 게시글/댓글 관리
    BO_POST_NOT_FOUND = {"code": "ERR-5201", "message": "게시글을 찾을 수 없습니다."}
    BO_COMMENT_NOT_FOUND = {"code": "ERR-5202", "message": "댓글을 찾을 수 없습니다."}

    # 5301~5302: 신고 관리
    BO_COMPLAINT_NOT_FOUND = {"code": "ERR-5301", "message": "신고를 찾을 수 없습니다."}
    BO_COMPLAINT_ALREADY_RESOLVED = {"code": "ERR-5302", "message": "이미 처리된 신고입니다."}

    # 5401~5402: 메뉴 관리
    BO_MENU_NOT_FOUND = {"code": "ERR-5401", "message": "메뉴를 찾을 수 없습니다."}
    BO_MENU_GROUP_NOT_FOUND = {"code": "ERR-5402", "message": "메뉴 그룹을 찾을 수 없습니다."}

    # 5403~5405: 광고 관리
    BO_AD_SLOT_NOT_FOUND = {"code": "ERR-5403", "message": "광고 슬롯을 찾을 수 없습니다."}
    BO_AD_SLOT_INACTIVE = {"code": "ERR-5404", "message": "비활성 상태인 광고 슬롯입니다."}
    BO_AD_NOT_FOUND = {"code": "ERR-5405", "message": "광고를 찾을 수 없습니다."}

    # 5107~5108: 가입 승인 관리
    BO_APPROVAL_NOT_FOUND = {"code": "ERR-5107", "message": "가입 신청을 찾을 수 없습니다."}
    BO_APPROVAL_ALREADY_PROCESSED = {"code": "ERR-5108", "message": "이미 처리된 가입 신청입니다."}

    # 5601: 알림 템플릿 관리
    BO_NOTIFICATION_TEMPLATE_NOT_FOUND = {"code": "ERR-5601", "message": "알림 템플릿을 찾을 수 없습니다."}

    # 5501~5503: 대학 관리
    BO_UNIVERSITY_NOT_FOUND = {"code": "ERR-5501", "message": "대학을 찾을 수 없습니다."}
    BO_UNIVERSITY_DUPLICATE_PUBLIC_ID = {"code": "ERR-5502", "message": "이미 사용 중인 대학 식별자입니다."}
    BO_UNIVERSITY_DUPLICATE_NAME = {"code": "ERR-5503", "message": "이미 등록된 대학명입니다."}

    # 4050번대: 커피챗
    COFFEECHAT_ROUND_NOT_FOUND = {"code": "ERR-4050", "message": "커피챗 라운드를 찾을 수 없습니다."}
    COFFEECHAT_ROUND_NOT_RECRUITING = {"code": "ERR-4051", "message": "모집 중인 라운드가 아닙니다."}
    COFFEECHAT_ALREADY_APPLIED = {"code": "ERR-4052", "message": "이미 신청한 라운드입니다."}
    COFFEECHAT_APPLICATION_NOT_FOUND = {"code": "ERR-4053", "message": "커피챗 신청을 찾을 수 없습니다."}
    COFFEECHAT_ALREADY_MATCHED = {"code": "ERR-4054", "message": "이미 매칭이 완료된 라운드입니다."}
    COFFEECHAT_LIMIT_EXCEEDED = {"code": "ERR-4055", "message": "동시에 참여할 수 있는 커피챗 수를 초과했습니다."}
    COFFEECHAT_EXPIRED = {"code": "ERR-4056", "message": "만료된 커피챗입니다."}
    COFFEECHAT_NOT_FOUND = {"code": "ERR-4057", "message": "커피챗을 찾을 수 없습니다."}
    COFFEECHAT_CONTINUE_ALREADY_REQUESTED = {"code": "ERR-4058", "message": "이미 이어가기를 요청했습니다."}
    COFFEECHAT_CONTINUE_NOT_REQUESTED = {"code": "ERR-4059", "message": "이어가기 요청이 없습니다."}
    COFFEECHAT_ALREADY_REVEALED = {"code": "ERR-4060", "message": "이미 실명 전환된 커피챗입니다."}
    COFFEECHAT_MIN_PARTICIPANTS_NOT_MET = {"code": "ERR-4061", "message": "최소 참여 인원이 충족되지 않았습니다."}
    COFFEECHAT_DISABLED = {"code": "ERR-4062", "message": "커피챗 수신이 비활성화되어 있습니다."}
    COFFEECHAT_CANCEL_AFTER_MATCH = {"code": "ERR-4063", "message": "매칭 이후에는 신청을 취소할 수 없습니다."}

    # 6000번대: 매칭
    MATCHING_SESSION_NOT_FOUND = {"code": "ERR-6001", "message": "매칭 세션을 찾을 수 없습니다."}
    MATCHING_SESSION_NOT_DRAFT = {"code": "ERR-6002", "message": "DRAFT 상태의 세션만 수정할 수 있습니다."}
    MATCHING_SESSION_NOT_MATCHED = {"code": "ERR-6003", "message": "매칭 실행 후 확정할 수 있습니다."}
    MATCHING_SESSION_ALREADY_CONFIRMED = {"code": "ERR-6004", "message": "이미 확정된 세션입니다."}
    MATCHING_SESSION_NOT_OPEN = {"code": "ERR-6005", "message": "신청 가능한 세션이 아닙니다."}
    MATCHING_ALREADY_APPLIED = {"code": "ERR-6006", "message": "이미 신청한 세션입니다."}
    MATCHING_APPLY_NOT_FOUND = {"code": "ERR-6007", "message": "신청 정보를 찾을 수 없습니다."}
    MATCHING_POOL_EMPTY = {"code": "ERR-6008", "message": "매칭 풀이 비어 있습니다."}
    MATCHING_RESULT_NOT_FOUND = {"code": "ERR-6009", "message": "매칭 결과를 찾을 수 없습니다."}
    MATCHING_POOL_ENTRY_NOT_FOUND = {"code": "ERR-6010", "message": "풀 참여자를 찾을 수 없습니다."}
