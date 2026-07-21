// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "AI_REMainUI.generated.h"

class UAI_REStatePointBar;
class UAI_REStatusComponent;
class UImage;
/**
 * 
 */

UCLASS()
class AI_RE_API UAI_REMainUI : public UUserWidget
{
	GENERATED_BODY()
	
private:
	UFUNCTION(BlueprintCallable)
	void UpdateHPBar(float Current, float Max);
	
	UFUNCTION(BlueprintCallable)
	void UpdateSPBar(float Current, float Max);
	
	UFUNCTION(BlueprintCallable)
	void UpdateHungerBar(float Current, float Max);
	
	// 타이머를 켜고 끌 때 필요한 리모콘(핸들)
	FTimerHandle HPSmoothTimerHandle;
	
protected:
	UPROPERTY(meta=(BindWidget))
	TObjectPtr<UAI_REStatePointBar> HPBar;
	
	UPROPERTY(meta=(BindWidget))
	TObjectPtr<UAI_REStatePointBar> SPBar;
	
	UPROPERTY(meta=(BindWidget))
	TObjectPtr<UAI_REStatePointBar> HungerBar;
	
public:
	UFUNCTION(BlueprintCallable)
	void InitializeHUD(TObjectPtr<UAI_REStatusComponent> InStatus);
	
	
	
};
