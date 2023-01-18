from struct import pack
from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.messages.flat.QuickChatSelection import QuickChatSelection
from rlbot.utils.structures.game_data_struct import GameTickPacket

from util.ball_prediction_analysis import find_slice_at_time
from util.boost_pad_tracker import BoostPadTracker
from util.drive import steer_toward_target
from util.sequence import Sequence, ControlStep
from util.vec import Vec3


class KevBot(BaseAgent):

    def __init__(self, name, team, index):
        super().__init__(name, team, index)
        self.sequence: Sequence = None
        self.boostPadTracker = BoostPadTracker()


    def initialize_agent(self):
        self.boostPadTracker.initialize_boosts(self.get_field_info())

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:

        # Info Updates
        self.boostPadTracker.update_boost_status(packet)

        # Check if theres a sequence of instructions currently active if so return next step
        if self.sequence is not None and not self.sequence.done:
            controls = self.sequence.tick(packet)
            if controls is not None:
                return controls

        # Make our controller we use to input instructions every tick
        controller = SimpleControllerState()

        # basic car information
        car = packet.game_cars[self.index]
        carLocation = Vec3(car.physics.location)
        carVelocity = Vec3(car.physics.velocity)

        # basic ball information
        ballLocation = Vec3(packet.game_ball.physics.location)
        ballVelocity = Vec3(packet.game_ball.physics.velocity)

        # basic controller commands
        controller.throttle = 1
        controller.steer = 0
        controller.pitch = 0
        controller.yaw = 0
        controller.roll = 0
        controller.jump = False
        controller.boost = False
        controller.handbrake = False

        # My Variables
        targetLocation = ballLocation

        # Basic Ball Prediction
        ballPrediction = self.get_ball_prediction_struct()
        ballInFuture = find_slice_at_time(ballPrediction,packet.game_info.seconds_elapsed +2)
        # Make sure it doesn't break when none (like replays or menu's)
        if ballInFuture is not None:
            targetLocation = Vec3(ballInFuture.physics.location)
            self.renderer.draw_line_3s(ballLocation,targetLocation,self.renderer.cyan())


        # Drawing some cool stuff
        self.renderer.draw_line_3d(carLocation, targetLocation, self.renderer.white())
        self.renderer.draw_string_3d(carLocation, 1, 1, f'Speed: {carVelocity.length():.1f}', self.renderer.white())
        self.renderer.draw_rect_3d(targetLocation, 8, 8, True, self.renderer.cyan(), centered=True)

        controller.steer = steer_toward_target(car,targetLocation)


        if False:
            # Talking
            self.send_quick_chat(team_only=False, quick_chat=QuickChatSelection.Information_IGotIt)
            
            # Call example front flip sequence method
            return self.begin_front_flip(packet)
            

        return controller

    def begin_front_flip(self, packet):

            
            # Do a front flip
            self.sequence = Sequence([
                ControlStep(duration=0.05, controls=SimpleControllerState(jump=True)),
                ControlStep(duration=0.05, controls=SimpleControllerState(jump=False)),
                ControlStep(duration=0.2, controls=SimpleControllerState(jump=True, pitch=-1)),
                ControlStep(duration=0.8, controls=SimpleControllerState()),
            ])

        # Return the controls associated with the beginning of the sequence so we can start right away.
            return self.sequence.tick(packet)



