"""
Core domain models
"""
from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, field_validator
from app.domain.enums import (
    SourceType,
    DifficultyLevel,
    PermissionLevel,
    ContributionType,
    FeaturedType,
    SubscriptionStatus,
    CreditType,
    CreditTransactionReason,
    ReferralSource,
)


# ============= Recipe Models =============

class Ingredient(BaseModel):
    """Single ingredient with quantity and unit"""
    name: str
    quantity: Optional[float] = None
    unit: Optional[str] = None
    notes: Optional[str] = None  # e.g., "finely chopped"
    group: Optional[str] = None  # e.g., "For the sauce"


class Instruction(BaseModel):
    """Single cooking instruction step"""
    step_number: int
    title: str
    description: str
    timer_minutes: Optional[float] = None  # If this step requires a timer (supports decimals like 0.5 for 30 seconds)
    group: Optional[str] = None  # e.g., "For the sauce", "Assembly"


class RecipeTimings(BaseModel):
    """Recipe timing information"""
    prep_time_minutes: Optional[int] = None
    cook_time_minutes: Optional[int] = None
    resting_time_minutes: Optional[int] = None  # Marinating, rising, freezing, cooling
    total_time_minutes: Optional[int] = None

    @field_validator('total_time_minutes')
    @classmethod
    def validate_total_time(cls, v, info):
        """Ensure total time is consistent with prep + cook + resting"""
        prep = info.data.get('prep_time_minutes') or 0
        cook = info.data.get('cook_time_minutes') or 0
        resting = info.data.get('resting_time_minutes') or 0
        if (prep or cook or resting) and not v:
            return prep + cook + resting
        return v


class Recipe(BaseModel):
    """Complete recipe model"""
    id: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    image_url: Optional[str] = None

    # Recipe content
    ingredients: List[Ingredient] = Field(default_factory=list)
    instructions: List[Instruction] = Field(default_factory=list)

    # Metadata
    servings: Optional[int] = Field(None, ge=1)
    difficulty: Optional[DifficultyLevel] = None
    tags: List[str] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)

    # Timings
    timings: Optional[RecipeTimings] = None

    # Source information
    source_type: SourceType
    source_url: Optional[str] = None

    # Attribution & forking
    created_by: str  # user_id
    original_recipe_id: Optional[str] = None  # If this is a fork
    fork_count: int = 0

    # Rating aggregation (half-star support)
    average_rating: Optional[float] = Field(None, ge=0.5, le=5.0)
    rating_count: int = 0
    rating_distribution: Optional[Dict[str, int]] = Field(
        default_factory=lambda: {
            "0.5": 0, "1": 0, "1.5": 0, "2": 0, "2.5": 0,
            "3": 0, "3.5": 0, "4": 0, "4.5": 0, "5": 0
        }
    )

    # Privacy
    is_public: bool = True

    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class RecipeContributor(BaseModel):
    """Tracks contributors to a recipe (for fork chains)"""
    recipe_id: str
    user_id: str
    user_email: Optional[str] = None
    contribution_type: ContributionType
    order: int  # Order in the contribution chain
    created_at: Optional[datetime] = None


class UserRecipeData(BaseModel):
    """User-specific recipe customizations and data"""
    user_id: str
    recipe_id: str

    # Custom ratings and timings (half-star support: 0.5, 1.0, 1.5, ..., 5.0)
    rating: Optional[float] = Field(None, ge=0.5, le=5.0)
    custom_prep_time_minutes: Optional[int] = None
    custom_cook_time_minutes: Optional[int] = None
    custom_resting_time_minutes: Optional[int] = None
    custom_difficulty: Optional[DifficultyLevel] = None

    # Personal notes
    notes: Optional[str] = None
    custom_servings: Optional[int] = None

    # Tracking
    times_cooked: int = 0
    last_cooked_at: Optional[datetime] = None
    is_favorite: bool = False
    was_extracted: bool = False  # True if user extracted/imported this recipe

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ============= Cookbook Models =============

class Cookbook(BaseModel):
    """Recipe collection/cookbook"""
    id: Optional[str] = None
    user_id: str
    title: str = Field(..., min_length=1, max_length=200)
    subtitle: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    image_url: Optional[str] = None

    # Privacy & sharing
    is_public: bool = False

    # Metadata
    recipe_count: int = 0

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CookbookFolder(BaseModel):
    """Folder within a cookbook for organizing recipes"""
    id: Optional[str] = None
    cookbook_id: str
    parent_folder_id: Optional[str] = None  # For nested folders
    name: str = Field(..., min_length=1, max_length=100)
    order: int = 0

    created_at: Optional[datetime] = None


class CookbookRecipe(BaseModel):
    """Link between cookbook and recipe"""
    cookbook_id: str
    recipe_id: str
    order: int = 0
    added_at: Optional[datetime] = None


class FolderRecipe(BaseModel):
    """Link between folder and recipe"""
    folder_id: str
    recipe_id: str
    order: int = 0
    added_at: Optional[datetime] = None


# ============= Sharing Models =============

class RecipeShare(BaseModel):
    """Sharing a recipe with specific users"""
    id: Optional[str] = None
    recipe_id: str
    shared_by_user_id: str
    shared_with_user_id: str
    permission_level: PermissionLevel

    created_at: Optional[datetime] = None


class CookbookShare(BaseModel):
    """Sharing a cookbook with specific users"""
    id: Optional[str] = None
    cookbook_id: str
    shared_by_user_id: str
    shared_with_user_id: str
    permission_level: PermissionLevel

    created_at: Optional[datetime] = None


# ============= Featured Recipes =============

class FeaturedRecipe(BaseModel):
    """Featured recipe for homepage"""
    id: Optional[str] = None
    recipe_id: str
    featured_type: FeaturedType
    priority: int = 0  # Higher = shown first
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    created_at: Optional[datetime] = None


# ============= Extraction Models =============

class ExtractionJob(BaseModel):
    """Recipe extraction job tracking"""
    id: Optional[str] = None
    user_id: str
    source_type: SourceType
    source_url: Optional[str] = None
    status: str  # pending, processing, completed, failed

    # Results
    recipe_id: Optional[str] = None  # Created recipe
    error_message: Optional[str] = None

    # Progress tracking
    progress_percentage: int = 0
    current_step: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ============= Subscription Models =============

class UserSubscription(BaseModel):
    """User subscription status synced from RevenueCat"""
    id: Optional[str] = None
    user_id: str
    revenuecat_customer_id: str
    product_id: Optional[str] = None  # e.g., 'cuisto_pro_monthly'
    entitlement_id: Optional[str] = None  # e.g., 'pro'
    is_active: bool = False
    expires_at: Optional[datetime] = None
    original_purchase_date: Optional[datetime] = None
    is_trial: bool = False

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SubscriptionStatusResponse(BaseModel):
    """Response for subscription status endpoint"""
    status: SubscriptionStatus
    is_premium: bool
    is_trialing: bool
    product_id: Optional[str] = None
    expires_at: Optional[datetime] = None
    will_renew: bool = False


# ============= Credits Models =============

class UserCredits(BaseModel):
    """User credit balance"""
    id: Optional[str] = None
    user_id: str
    standard_credits: int = 5
    referral_credits: int = 0
    credits_reset_at: Optional[datetime] = None
    first_week_ends_at: Optional[datetime] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CreditsResponse(BaseModel):
    """Response for credits endpoint"""
    standard_credits: int
    referral_credits: int
    total_credits: int
    is_first_week: bool
    next_reset_at: Optional[datetime] = None
    can_extract: bool
    is_premium: bool


class ReferralCreditGrant(BaseModel):
    """Individual referral credit grant with expiry"""
    id: Optional[str] = None
    user_id: str
    amount: int
    remaining: int
    source: ReferralSource
    expires_at: datetime

    created_at: Optional[datetime] = None


class CreditTransaction(BaseModel):
    """Credit transaction log entry"""
    id: Optional[str] = None
    user_id: str
    amount: int  # Positive = add, negative = deduct
    credit_type: CreditType
    reason: CreditTransactionReason
    extraction_job_id: Optional[str] = None
    balance_after: int

    created_at: Optional[datetime] = None


# ============= Referral Models =============

class ReferralCode(BaseModel):
    """User's referral code"""
    id: Optional[str] = None
    user_id: str
    code: str
    uses_count: int = 0

    created_at: Optional[datetime] = None


class ReferralRedemption(BaseModel):
    """Record of a referral code being used"""
    id: Optional[str] = None
    referrer_user_id: str
    referee_user_id: str
    referral_code_id: str
    credits_awarded: int = 5

    created_at: Optional[datetime] = None


class ReferralStats(BaseModel):
    """User's referral statistics"""
    code: str
    uses_count: int
    total_credits_earned: int
    pending_referral_credits: int  # Credits not yet expired


class ReferralCodeValidation(BaseModel):
    """Response for referral code validation"""
    is_valid: bool
    message: str
    referrer_name: Optional[str] = None
