// src/services/lessonPlanService.ts
import type { LessonPlanFormData, GenerationRequest } from '@/types'
import { useMainStore } from '@/store'
import type { ContentType } from '@/core/constants'

export class LessonPlanService {
  private store = useMainStore()

  async generateLessonPlan(formData: LessonPlanFormData): Promise<string> {
    try {
      const prompt = await this.formatPrompt(formData)

      const request: GenerationRequest = {
        user_id: this.store.user?.id,
        type: 'lesson_plan' as ContentType,
        prompt
      }

      const response = await this.store.generateContent(request)

      if (response && typeof response === 'string') {
        return response
      }

      throw new Error('Failed to generate lesson plan')
    } catch (error) {
      console.error('Error in lesson plan generation:', error)
      throw error
    }
  }

  private async formatPrompt(data: LessonPlanFormData): Promise<string> {
    // Преобразуем данные формы в формат, понятный текущему генератору
    const prompt = {
      language: data.language,
      topic: data.topic,
      text_content: data.topic,
      level: data.level,
      duration: data.duration,
      methodologies: {
        main: data.methodologies.mainMethod,
        support: data.methodologies.supportMethods.join(', ')
      },
      objectives: data.objectives,
      materials: data.materials,
      assessment_type: data.assessment,
      format: data.format,
      include_cultural_elements: data.culturalElements
    }

    console.log('Formatted prompt for lesson plan:', JSON.stringify(prompt, null, 2));

    return JSON.stringify(prompt)
  }
}

export const lessonPlanService = new LessonPlanService()
