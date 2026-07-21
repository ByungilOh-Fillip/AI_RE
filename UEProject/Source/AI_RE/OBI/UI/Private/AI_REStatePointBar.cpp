// Fill out your copyright notice in the Description page of Project Settings.


#include "AI_REStatePointBar.h"
#include "TimerManager.h"
#include "Components/Image.h"
#include "Materials/MaterialInstanceDynamic.h"

void UAI_REStatePointBar::SmoothBar()
{
	CurrentPercent = FMath::FInterpTo(CurrentPercent, TargetPercent, 0.016f, 5.0f);
	StateBar->GetDynamicMaterial()->SetScalarParameterValue(FName("Percent"), CurrentPercent);
	
	if (FMath::IsNearlyEqual(CurrentPercent, TargetPercent,0.001f)) 
	{ 
		CurrentPercent = TargetPercent; 
    
		StateBar->GetDynamicMaterial()->SetScalarParameterValue(FName("Percent"), CurrentPercent);
    
		GetWorld()->GetTimerManager().ClearTimer(SmoothTimerHandle);
	}

}

void UAI_REStatePointBar::SetTargetPercent(float NewPercent)
{
	TargetPercent = NewPercent;
	GetWorld()->GetTimerManager().SetTimer(SmoothTimerHandle, this, &UAI_REStatePointBar::SmoothBar, 0.016f, true);
}
