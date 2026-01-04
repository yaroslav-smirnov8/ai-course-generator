// types/settings.ts

export interface SystemSettings {
  tariffs: TariffSetting[];
  referral: ReferralSettings;
}

export interface TariffSetting {
  type: string;
  name: string;
  settings: {
    generations_limit: number;
    images_limit: number;
    price_points: number;
  };
}

export interface ReferralSettings {
  new_user_discount: number;
  referrer_discount: number;
  max_discount: number;
}
