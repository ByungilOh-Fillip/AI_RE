// Copyright MixUpProject. All Rights Reserved.

#include "PlayerCombatComponent.h"

#include "DrawDebugHelpers.h"
#include "TimerManager.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"

UPlayerCombatComponent::UPlayerCombatComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
}

void UPlayerCombatComponent::BeginPlay()
{
	Super::BeginPlay();
}

void UPlayerCombatComponent::TryStartPrimaryAction()
{
	if (bIsActionActive) return;

	bIsActionActive = true;

	// In single player, instantly perform the hit for maximum responsiveness.
	// We can hook up AnimNotifies to trigger PerformTraceHit() later for animation sync.
	PerformTraceHit();

	// Automatically end the action after a short duration (placeholder for animation length).
	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().SetTimer(ActionTimerHandle, [this]() { TryStopPrimaryAction(); }, 0.5f, false);
	}
}

void UPlayerCombatComponent::TryStopPrimaryAction()
{
	bIsActionActive = false;
	
	if (UWorld* World = GetWorld())
	{
		World->GetTimerManager().ClearTimer(ActionTimerHandle);
	}
}

void UPlayerCombatComponent::PerformTraceHit()
{
	APawn* OwnerPawn = Cast<APawn>(GetOwner());
	if (!OwnerPawn) return;

	APlayerController* PC = Cast<APlayerController>(OwnerPawn->GetController());
	if (!PC) return;

	FVector ViewLocation;
	FRotator ViewRotation;
	PC->GetPlayerViewPoint(ViewLocation, ViewRotation);

	FVector TraceStart = ViewLocation;
	FVector TraceEnd = TraceStart + (ViewRotation.Vector() * TraceDistance);

	FHitResult HitResult;
	FCollisionQueryParams QueryParams;
	QueryParams.AddIgnoredActor(OwnerPawn);

	if (GetWorld()->LineTraceSingleByChannel(HitResult, TraceStart, TraceEnd, ECC_Visibility, QueryParams))
	{
		AActor* HitActor = HitResult.GetActor();
		if (HitActor)
		{
			// Optional: draw debug line
			DrawDebugLine(GetWorld(), TraceStart, HitResult.ImpactPoint, FColor::Red, false, 2.0f);
			DrawDebugPoint(GetWorld(), HitResult.ImpactPoint, 10.0f, FColor::Green, false, 2.0f);

			// Apply simple damage (later connect to harvest interfaces or health components)
			// ...
			
			OnPrimaryActionHit.Broadcast(HitActor);
		}
	}
}
