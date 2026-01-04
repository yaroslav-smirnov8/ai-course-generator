// Экспортируем компоненты формы
export { default as DsInput } from './DsInput.vue';
export { default as DsSelect } from './DsSelect.vue';
export { default as DsTextarea } from './DsTextarea.vue';
export { default as DsButton } from './DsButton.vue';

// Типы для компонентов
export interface SelectOption {
  value: string;
  label: string;
}

export interface ButtonProps {
  text: string;
  variant?: 'primary' | 'secondary' | 'submit' | 'icon';
  size?: 'sm' | 'md' | 'lg';
  icon?: string;
  type?: 'button' | 'submit' | 'reset';
  disabled?: boolean;
  loading?: boolean;
  fullWidth?: boolean;
} 