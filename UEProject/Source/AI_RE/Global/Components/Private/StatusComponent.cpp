#include "StatusComponent.h"

UStatusComponent::UStatusComponent()
{
	PrimaryComponentTick.bCanEverTick = true;

    // 디폴트 스탯 세팅
	MaxHP = 100.f;
	CurrentHP = MaxHP;
	
	MaxSP = 100.f;
	CurrentSP = MaxSP;
	
	MaxHunger = 100.f;
	CurrentHunger = MaxHunger;

	Attack = 10.f;
	Defense = 10.f;
	WorkSpeed = 1.0f;
}

void UStatusComponent::BeginPlay()
{
	Super::BeginPlay();

    // 시작 시 UI 업데이트용 델리게이트 브로드캐스트
	OnHPChanged.Broadcast(CurrentHP, MaxHP);
	OnSPChanged.Broadcast(CurrentSP, MaxSP);
	OnHungerChanged.Broadcast(CurrentHunger, MaxHunger);
}

void UStatusComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
}

void UStatusComponent::ConsumeSP(float Amount)
{
    CurrentSP = FMath::Clamp(CurrentSP - Amount, 0.f, MaxSP);
    OnSPChanged.Broadcast(CurrentSP, MaxSP);
}

void UStatusComponent::ApplyDamage(float Amount)
{
    float ActualDamage = FMath::Max(Amount - Defense, 1.f);
    CurrentHP = FMath::Clamp(CurrentHP - ActualDamage, 0.f, MaxHP);
    OnHPChanged.Broadcast(CurrentHP, MaxHP);
}
