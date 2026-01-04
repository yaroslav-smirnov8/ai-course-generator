// src/services/tariffService.ts

import { apiClient } from '@/api';
import type { TariffInfo, UserTariffHistory } from '@/types';
import type { TariffType } from '@/core/constants';

/**
 * Сервис для работы с тарифами пользователей
 */
export const tariffService = {
  /**
   * Получить информацию о текущем тарифе пользователя
   */
  async getUserTariff(userId: number): Promise<TariffInfo | null> {
    try {
      const response = await apiClient.get(`/api/v1/users/${userId}/tariff`);
      return response.data;
    } catch (error) {
      console.error('Error fetching user tariff:', error);
      return null;
    }
  },

  /**
   * Обновить тариф пользователя
   */
  async updateUserTariff(userId: number, tariffType: TariffType): Promise<boolean> {
    try {
      await apiClient.post(`/api/v1/users/${userId}/tariff`, {
        tariff_type: tariffType
      });
      return true;
    } catch (error) {
      console.error('Error updating user tariff:', error);
      throw error;
    }
  },

  /**
   * Получить историю тарифов пользователя
   */
  async getTariffHistory(userId: number): Promise<UserTariffHistory[]> {
    try {
      const response = await apiClient.get(`/api/v1/users/${userId}/tariff/history`);
      return response.data;
    } catch (error) {
      console.error('Error fetching tariff history:', error);
      return [];
    }
  },

  /**
   * Проверить активность тарифа
   */
  async checkTariffValidity(userId: number): Promise<boolean> {
    try {
      const response = await apiClient.get(`/api/v1/users/${userId}/tariff/check`);
      return response.data.is_valid;
    } catch (error) {
      console.error('Error checking tariff validity:', error);
      return false;
    }
  },

  /**
   * Продлить текущий тариф
   */
  async extendTariff(userId: number, months: number = 1): Promise<boolean> {
    try {
      await apiClient.post(`/api/v1/users/${userId}/tariff/extend`, {
        months
      });
      return true;
    } catch (error) {
      console.error('Error extending tariff:', error);
      throw error;
    }
  },

  /**
   * Получить доступные тарифы
   */
  async getAvailableTariffs(): Promise<TariffInfo[]> {
    try {
      const response = await apiClient.get('/api/v1/tariffs');
      return response.data;
    } catch (error) {
      console.error('Error fetching available tariffs:', error);
      return [];
    }
  }
};
