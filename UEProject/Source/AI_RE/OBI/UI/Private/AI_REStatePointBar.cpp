// Fill out your copyright notice in the Description page of Project Settings.


#include "AI_REStatePointBar.h"
#include "TimerManager.h"
#include "Components/Image.h"
#include "Materials/MaterialInstanceDynamic.h"

void UAI_REStatePointBar::SmoothBar()
{
	CurrentPercent = FMath::FInterpTo(CurrentPercent, TargetPercent, 0.016f, 5.0f);
	
	if (StateBar && StateBar->GetDynamicMaterial())
	{
		StateBar->GetDynamicMaterial()->SetScalarParameterValue(FName("Percent"), CurrentPercent);
	}
	
	if (FMath::IsNearlyEqual(CurrentPercent, TargetPercent,0.001f)) 
	{ 
		CurrentPercent = TargetPercent; 
		
		if (StateBar && StateBar->GetDynamicMaterial())
		{
			StateBar->GetDynamicMaterial()->SetScalarParameterValue(FName("Percent"), CurrentPercent);
		}
		
		GetWorld()->GetTimerManager().ClearTimer(SmoothTimerHandle);
	}

}

void UAI_REStatePointBar::NativePreConstruct()
{
	Super::NativePreConstruct();
	
	// 1. 에디터에서 사용자가 커스텀 머티리얼을 슬롯에 넣었다면?
	if (StateBar && CustomBarMaterial)
	{
		// 2. 해당 머티리얼을 이미지 브러시로 덮어씌웁니다.
		StateBar->SetBrushFromMaterial(CustomBarMaterial);
	}
}

void UAI_REStatePointBar::SetTargetPercent(float NewPercent)
{
	TargetPercent = NewPercent;

	GetWorld()->GetTimerManager().SetTimer(SmoothTimerHandle, this, &UAI_REStatePointBar::SmoothBar, 0.016f, true);
	
}
