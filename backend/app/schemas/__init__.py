# app/schemas/__init__.py
from .achievements import (
    AchievementBase,
    AchievementCreate,
    AchievementUpdate,
    AchievementResponse,
    UserAchievementBase,
    UserAchievementCreate,
    UserAchievementUpdate,
    UserAchievementResponse,
    AchievementProgress,
    AchievementCheckRequest
)

from .content import (
    ContentGeneration,
    ContentGenerationBase,
    GeneratedContent,
    ImageBase,
    ImageGenerationRequest,
    ImageResponseData,
    VideoTranscriptBase,
    VideoTranscriptRequest,
    VideoTranscriptResponse,
    ApiResponse,
    ContentResponse,
    ImageResponse,
    ErrorResponse,
    TranscriptSettings,
    ExerciseSettings,
    GameSettings
)

from .course import (
    ActivityBase,
    ActivityCreate,
    Activity,
    LessonBase,
    LessonCreate,
    Lesson,
    CourseBase,
    CourseCreate,
    CourseUpdate,
    Course,
    TemplateBase,
    TemplateCreate,
    Template
)

from .generations import (
    GenerationBase,
    GenerationCreate,
    GenerationResponse,
    GenerationListResponse,
    GenerationFilter
)

from .pricing import (
    SpecialOfferBase,
    SpecialOfferCreate,
    SpecialOfferUpdate,
    SpecialOffer,
    DiscountCreate,
    DiscountUpdate,
    Discount,
    PricingRuleCreate,
    PricingRuleUpdate,
    PricingRule,
    PriceCalculation,
    AppliedDiscountCreate,
    AppliedDiscount,
    TariffType,
    TariffInfo,
    TariffExtension,
    TariffBase,
    TariffCreate,
    TariffUpdate,
    TariffResponse,
    UserTariffHistory,
    DailyLimits,
    PriceChangeCreate
)

from .tracking import (
    UsageLogBase,
    UsageLogCreate,
    UsageLogResponse,
    DailyUsageBase,
    DailyUsageCreate,
    DailyUsageResponse,
    GenerationMetricsBase,
    GenerationMetricsCreate,
    GenerationMetricsResponse,
    UserActivityLogBase,
    UserActivityLogCreate,
    UserActivityLogResponse,
    UsageStatisticsBase,
    UsageStatisticsCreate,
    UsageStatisticsResponse
)

from .user import (
    TelegramUserData,
    UserBase,
    UserCreate,
    UserUpdate,
    UserInDB,
    UserList,
    UserStats,
    UserResponse
)


from .profile import (TelegramUserData, UserStatistics, UserProfile, UserSettings)

from .points import (
    PointBalanceResponse,
    PointTransactionCreate,
    PointTransactionResponse,
    BulkPointTransactionCreate,
    TransactionType,
    TransactionStatistics
)

from .points_purchase import (
    PurchaseResponse,
    PurchaseStatistics,
    PurchaseRequest,
    PurchaseRefund,
    PurchaseStatus,
    PurchaseHistory,
    PurchasePackage,
    PromotionalOffer,
    PurchaseConfirmation,
    PaymentMethod
)



__all__ = [
    # Achievements
    "AchievementBase",
    "AchievementCreate",
    "AchievementUpdate",
    "AchievementResponse",
    "UserAchievementBase",
    "UserAchievementCreate",
    "UserAchievementUpdate",
    "UserAchievementResponse",
    "AchievementProgress",
    "AchievementCheckRequest",

    # Content
    "ContentGeneration",
    "ContentGenerationBase",
    "GeneratedContent",
    "ImageBase",
    "ImageGenerationRequest",
    "ImageResponseData",
    "VideoTranscriptBase",
    "VideoTranscriptRequest",
    "VideoTranscriptResponse",
    "ApiResponse",
    "ContentResponse",
    "ImageResponse",
    "ErrorResponse",
    "TranscriptSettings",
    "ExerciseSettings",
    "GameSettings",

    # Course
    "ActivityBase",
    "ActivityCreate",
    "Activity",
    "LessonBase",
    "LessonCreate",
    "Lesson",
    "CourseBase",
    "CourseCreate",
    "CourseUpdate",
    "Course",
    "TemplateBase",
    "TemplateCreate",
    "Template",

    # Generations
    "GenerationBase",
    "GenerationCreate",
    "GenerationResponse",
    "GenerationListResponse",
    "GenerationFilter",

    # Pricing
    "SpecialOfferBase",
    "SpecialOfferCreate",
    "SpecialOfferUpdate",
    "SpecialOffer",
    "DiscountCreate",
    "DiscountUpdate",
    "Discount",
    "PricingRuleCreate",
    "PricingRuleUpdate",
    "PricingRule",
    "PriceCalculation",
    "AppliedDiscountCreate",
    "AppliedDiscount",
    "TariffType",
    "TariffInfo",
    "TariffExtension",
    "TariffBase",
    "TariffCreate",
    "TariffUpdate",
    "TariffResponse",
    "UserTariffHistory",
    "DailyLimits",
    "PriceChangeCreate",

    # Tracking
    "UsageLogBase",
    "UsageLogCreate",
    "UsageLogResponse",
    "DailyUsageBase",
    "DailyUsageCreate",
    "DailyUsageResponse",
    "GenerationMetricsBase",
    "GenerationMetricsCreate",
    "GenerationMetricsResponse",
    "UserActivityLogBase",
    "UserActivityLogCreate",
    "UserActivityLogResponse",
    "UsageStatisticsBase",
    "UsageStatisticsCreate",
    "UsageStatisticsResponse",

    # User
    "TelegramUserData",
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserInDB",
    "UserList",
    "UserStats",
    "UserResponse",

    # Profile
    "TelegramUserData",
    "UserStatistics",
    "UserProfile",
    "UserSettings",

    # Points
    "PointBalanceResponse",
    "PointTransactionCreate",
    "PointTransactionResponse",
    "BulkPointTransactionCreate",
    "TransactionType",
    "TransactionStatistics",

    # Points Purchase
    "PurchaseResponse",
    "PurchaseStatistics",
    "PurchaseRequest",
    "PurchaseRefund",
    "PurchaseStatus",
    "PurchaseHistory",
    "PurchasePackage",
    "PromotionalOffer",
    "PurchaseConfirmation",
    "PaymentMethod",
]